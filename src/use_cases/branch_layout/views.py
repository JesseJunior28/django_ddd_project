import uuid

from src.entities.branch.errors import BranchNotFoundError
from src.entities.branch_layout.errors import (BranchLayoutAlreadyExist, BranchLayoutNotFound,
    BranchLayoutVersionCodeValidationError, ElementConfigurationModuleConflict,
    ElementNonMarketingPointConflict, ElementPlanogramDepartmentConflict,
    LayoutElementNotFound, ModuleNonMarketingPointConflict)
from src.entities.branch_layout.models import ElementModuleConfiguration, LayoutElement
from src.entities.branch_layout.service import BranchLayoutService
from src.entities.planogram.models import Module, Planogram
from src.middlewares.auth import AuthenticatedController


def valid_id(value): return isinstance(value, int) and not isinstance(value, bool) and value > 0
def body_error(view): return view.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
def error(view, status, exc): return getattr(view, status)({"name": type(exc).__name__, "message": str(exc)})


def config_entity(config):
    result = {"layoutElementId": config.layout_element_id, "isMarketingPoint": config.is_marketing_point}
    if config.orientation: result["orientation"] = config.orientation
    if config.front_direction: result["frontDirection"] = config.front_direction
    if config.module_id:
        module = config.module
        zone, department, planogram = module.planogram.department.zone, module.planogram.department, module.planogram
        result["moduleId"] = module.id
        result["moduleDetails"] = {"planogramId": planogram.id, **({"planogramName": planogram.name} if planogram.name else {}), "moduleSequence": module.sequence, "zone": {"id": zone.id, "name": zone.name, "hexColor": zone.hex_color, "isMarketingZone": zone.is_marketing_zone, "department": {"id": department.id, "name": department.name}}}
    return result


def element_entity(item):
    result = {"id": item.id, "type": item.type, "branchLayoutId": item.branch_layout_id}
    if item.text: result["text"] = item.text
    try:
        rect = item.rect_element
        result["rectElement"] = {"layoutElementId": item.id, "positionX": rect.position_x, "positionY": rect.position_y, "width": rect.width, "height": rect.height, **({"rotation": rect.rotation} if rect.rotation is not None else {})}
    except item.__class__.rect_element.RelatedObjectDoesNotExist: pass
    try:
        line = item.line_element
        result["lineElement"] = {"layoutElementId": item.id, "x1": line.x1, "y1": line.y1, "x2": line.x2, "y2": line.y2}
    except item.__class__.line_element.RelatedObjectDoesNotExist: pass
    try: result["moduleConfiguration"] = config_entity(item.module_configuration)
    except item.__class__.module_configuration.RelatedObjectDoesNotExist: pass
    return result


def layout_entity(layout):
    return {"id": layout.id, "branchId": layout.branch_id, "version": layout.version, "createdAt": layout.created_at, "updatedAt": layout.updated_at, "elements": [element_entity(item) for item in layout.elements.all()]}


class AdminLayoutController(AuthenticatedController):
    authorized_roles = ("ADMIN",)


class BranchLayoutView(AdminLayoutController):
    def post(self, request):
        data = request.data
        if not isinstance(data, dict) or not valid_id(data.get("branchId")) or not isinstance(data.get("elements"), list):
            if data == {}:
                return self.bad_request({"name": "InputValidationError", "message": "ID da loja é obrigatório, Os elementos da planta são obrigatórios"})
            return body_error(self)
        try:
            layout = BranchLayoutService().create(data["branchId"], data["elements"])
            if not layout: return error(self, "not_found", BranchNotFoundError(data["branchId"]))
            return self.created(layout_entity(BranchLayoutService().get(data["branchId"])))
        except BranchLayoutAlreadyExist as exc: return error(self, "conflict", exc)

    def put(self, request):
        data = request.data
        try: uuid.UUID(data.get("versionCode", ""))
        except (ValueError, TypeError, AttributeError): return body_error(self)
        if not isinstance(data, dict) or not valid_id(data.get("branchId")) or not isinstance(data.get("elements"), list): return body_error(self)
        try: return self.ok(layout_entity(BranchLayoutService().edit(data["branchId"], data["versionCode"], data["elements"])))
        except BranchLayoutNotFound as exc: return error(self, "not_found", exc)
        except BranchLayoutVersionCodeValidationError as exc: return error(self, "bad_request", exc)


class GetBranchLayoutView(AuthenticatedController):
    def get(self, request):
        raw = request.query_params.get("branchId")
        if not raw or not raw.isdigit():
            return self.bad_request({"name": "InputValidationError", "message": "Tipo inválido para o id da loja"})
        layout = BranchLayoutService().get(int(raw))
        if not layout: return error(self, "not_found", BranchLayoutNotFound(raw))
        return self.ok(layout_entity(layout))


class DeleteBranchLayoutView(AdminLayoutController):
    def delete(self, request, branch_id):
        if not branch_id.isdigit(): return body_error(self)
        try: BranchLayoutService().delete(int(branch_id))
        except BranchLayoutNotFound as exc: return error(self, "not_found", exc)
        return self.no_content()


class GenerateLayoutVersionCodeView(AdminLayoutController):
    def post(self, request):
        branch_id = request.data.get("branchId") if isinstance(request.data, dict) else None
        if not valid_id(branch_id): return body_error(self)
        try: return self.ok({"versionCode": BranchLayoutService().generate_version_code(branch_id)})
        except BranchLayoutNotFound as exc: return error(self, "not_found", exc)


class ElementModuleConfigurationView(AdminLayoutController):
    def put(self, request):
        data = request.data
        if not isinstance(data, dict) or not valid_id(data.get("layoutElementId")) or not isinstance(data.get("isMarketingPoint"), bool) or ("moduleId" in data and not valid_id(data["moduleId"])) or ("orientation" in data and data["orientation"] not in ("LEFT_TO_RIGHT", "RIGHT_TO_LEFT")): return body_error(self)
        try: result = BranchLayoutService().upsert_module_configuration(data)
        except LayoutElementNotFound as exc: return error(self, "not_found", exc)
        except (ElementConfigurationModuleConflict, ElementNonMarketingPointConflict, ElementPlanogramDepartmentConflict, ModuleNonMarketingPointConflict) as exc: return error(self, "conflict", exc)
        if isinstance(result, tuple): return self.not_found({"name": "ModuleNotFound", "message": f"Módulo com id {result[1]} não foi encontrado."})
        result = ElementModuleConfiguration.objects.select_related("module__planogram__department__zone").get(pk=result.pk)
        return self.ok(config_entity(result))


class GetBranchesByPlanogramView(AdminLayoutController):
    def get(self, request):
        raw = request.query_params.get("planogramId")
        if not raw or not raw.isdigit(): return body_error(self)
        from src.entities.branch.models import Branch
        rows = Branch.objects.filter(layout__elements__module_configuration__module__planogram_id=int(raw)).distinct().order_by("id")
        return self.ok({"results": [{"id": item.id, "name": item.name, "city": item.city, "uf": item.uf, "address": item.address, "hasLayout": True, "createdAt": item.created_at, "updatedAt": item.updated_at} for item in rows]})
