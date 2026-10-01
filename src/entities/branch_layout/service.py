import uuid

from django.db import transaction

from src.entities.branch.models import Branch
from src.entities.planogram.models import Module

from .errors import (BranchLayoutAlreadyExist, BranchLayoutNotFound,
                     BranchLayoutVersionCodeValidationError,
                     ElementConfigurationModuleConflict,
                     ElementNonMarketingPointConflict,
                     ElementPlanogramDepartmentConflict, LayoutElementNotFound,
                     ModuleNonMarketingPointConflict)
from .models import BranchLayout, ElementModuleConfiguration, LayoutElement, LineElement, RectElement


def front_direction(rotation):
    if rotation < 45: return "DOWN"
    if rotation < 130: return "LEFT"
    if rotation < 230: return "UP"
    if rotation < 315: return "RIGHT"
    return "DOWN"


class BranchLayoutService:
    def get(self, branch_id, *, lock=False):
        query = BranchLayout.objects
        if lock: query = query.select_for_update()
        return query.select_related("branch").prefetch_related(
            "elements__rect_element", "elements__line_element",
            "elements__module_configuration__module__planogram__department__zone",
        ).filter(branch_id=branch_id).first()

    def create(self, branch_id, elements):
        with transaction.atomic():
            if not Branch.objects.filter(pk=branch_id).exists():
                return None
            if BranchLayout.objects.select_for_update().filter(branch_id=branch_id).exists():
                raise BranchLayoutAlreadyExist(branch_id)
            layout = BranchLayout.objects.create(branch_id=branch_id)
            for element in elements:
                self.create_element(layout, element)
            return layout

    @staticmethod
    def create_element(layout, data):
        element = LayoutElement.objects.create(branch_layout=layout, type=data["type"], text=data.get("text"))
        rect = data.get("rectElement")
        if rect is not None:
            RectElement.objects.create(layout_element=element, position_x=rect["positionX"], position_y=rect["positionY"], width=rect["width"], height=rect["height"], rotation=rect.get("rotation"))
        line = data.get("lineElement")
        if line is not None:
            LineElement.objects.create(layout_element=element, x1=line["x1"], y1=line["y1"], x2=line["x2"], y2=line["y2"])
        return element

    def generate_version_code(self, branch_id):
        with transaction.atomic():
            layout = self.get(branch_id, lock=True)
            if not layout: raise BranchLayoutNotFound(branch_id)
            layout.version_code = uuid.uuid4()
            layout.save(update_fields=["version_code", "updated_at"])
            return str(layout.version_code)

    def edit(self, branch_id, version_code, elements):
        with transaction.atomic():
            layout = self.get(branch_id, lock=True)
            if not layout: raise BranchLayoutNotFound(branch_id)
            if str(layout.version_code) != version_code: raise BranchLayoutVersionCodeValidationError(branch_id)
            old = {item.id: item for item in layout.elements.all()}
            kept = set()
            for data in elements:
                element_id = data.get("id")
                if not element_id:
                    self.create_element(layout, data)
                    continue
                element = old.get(element_id)
                if not element:  # Um elemento inexistente interrompe toda a atualização.
                    raise LayoutElementNotFound(element_id)
                kept.add(element_id)
                element.text = data.get("text")
                element.save(update_fields=["text"])
                rect = data.get("rectElement")
                if rect is not None:
                    RectElement.objects.update_or_create(layout_element=element, defaults={"position_x": rect["positionX"], "position_y": rect["positionY"], "width": rect["width"], "height": rect["height"], "rotation": rect.get("rotation")})
                    config = ElementModuleConfiguration.objects.filter(layout_element=element).first()
                    if config:
                        config.front_direction = front_direction(rect.get("rotation") or 0)
                        config.orientation = None
                        config.save(update_fields=["front_direction", "orientation"])
                line = data.get("lineElement")
                if line is not None:
                    LineElement.objects.update_or_create(layout_element=element, defaults={"x1": line["x1"], "y1": line["y1"], "x2": line["x2"], "y2": line["y2"]})
            LayoutElement.objects.filter(branch_layout=layout).exclude(pk__in=kept).delete()
            layout.version_code = None
            layout.version += 1
            layout.save(update_fields=["version_code", "version", "updated_at"])
            # As relações foram carregadas antes da reconciliação; recarrega a geometria persistida.
            return self.get(branch_id)

    def delete(self, branch_id):
        with transaction.atomic():
            layout = self.get(branch_id, lock=True)
            if not layout: raise BranchLayoutNotFound(branch_id)
            layout.delete()

    def upsert_module_configuration(self, data):
        with transaction.atomic():
            # PostgreSQL não bloqueia o lado anulável de um outer join. Bloqueia o
            # elemento principal e carrega sua geometria opcional em seguida.
            element = LayoutElement.objects.select_for_update(of=("self",)).select_related("rect_element").filter(pk=data["layoutElementId"]).first()
            if not element: raise LayoutElementNotFound(data["layoutElementId"])
            module_id = data.get("moduleId")
            module = Module.objects.select_related("planogram__department__zone").filter(pk=module_id).first() if module_id else None
            if module_id and not module: return "module-not-found", module_id
            if module:
                if not data["isMarketingPoint"] and module.planogram.department.zone.is_marketing_zone:
                    raise ElementNonMarketingPointConflict()
                if data["isMarketingPoint"] and not module.planogram.department.zone.is_marketing_zone:
                    raise ModuleNonMarketingPointConflict()
                # A condição evita recriar uma configuração já associada ao elemento.
                if not data["isMarketingPoint"]:
                    other = Module.objects.filter(
                        planogram__department_id=module.planogram.department_id,
                        element_module_configurations__layout_element__branch_layout_id=element.branch_layout_id,
                    ).exclude(planogram_id=module.planogram_id).select_related("planogram__department").first()
                    if other:
                        raise ElementPlanogramDepartmentConflict(other.planogram_id, module.planogram.department.name)
                    conflict = ElementModuleConfiguration.objects.filter(
                        module_id=module.id, layout_element__branch_layout_id=element.branch_layout_id,
                    ).exclude(layout_element_id=element.id).first()
                    if conflict:
                        raise ElementConfigurationModuleConflict(conflict.layout_element_id, module.id)
            direction = front_direction(element.rect_element.rotation) if getattr(element, "rect_element", None) and element.rect_element.rotation else None
            config, _ = ElementModuleConfiguration.objects.update_or_create(layout_element=element, defaults={"module": module, "is_marketing_point": data["isMarketingPoint"], "orientation": data.get("orientation"), "front_direction": direction})
            return config
