from django.db.models import Q

from src.entities.planogram.errors import (LevelsNotFound, MaxShelfWidthExceeded, ModuleNotFound, ModuleSequenceConflict, PlanogramDepartmentConflict, ShelfExistanceConflict, ShelfLevelExistanceConflict, ShelfLevelNotFound, ShelfLevelSequenceConflict, ShelfNotFound, ShelfSequenceConflict)
from src.entities.planogram.models import Module, Planogram, Shelf
from src.entities.planogram.service import PlanogramService
from src.entities.planogram.mounter import mount
from src.middlewares.auth import AuthenticatedController

EXPOSITION_TYPES = ("SHELF", "BASCKET", "BAR")


def valid_int(value, *, positive=False):
    return isinstance(value, int) and not isinstance(value, bool) and (not positive or value > 0)


def error(view, status, exc):
    return getattr(view, status)({"name": type(exc).__name__, "message": str(exc)})


def level_entity(item):
    level = item.level
    return {"id": item.id, "shelfId": item.shelf_id, "levelId": item.level_id, "width": item.width, "sequence": item.sequence, "expositionType": item.exposition_type, "level": {"id": level.id, "name": level.name, **({"label": level.label} if level.label else {}), "hexColor": level.hex_color, "divisions": level.divisions, "departmentId": level.department_id}}


def shelf_entity(shelf):
    return {"id": shelf.id, "moduleId": shelf.module_id, "sequence": shelf.sequence, "levels": [level_entity(item) for item in shelf.levels.select_related("level").order_by("sequence", "id")]}


def module_entity(module):
    return {"id": module.id, "planogramId": module.planogram_id, "sequence": module.sequence, "maxModuleWidth": module.width, "shelves": [shelf_entity(shelf) for shelf in module.shelves.all().order_by("sequence", "id")]}


def planogram_entity(planogram, *, branches_count=None, availability=False):
    department = planogram.department
    result = {"id": planogram.id, **({"name": planogram.name} if planogram.name else {}), "isActive": planogram.is_active, "departmentId": department.id, "department": {"id": department.id, "name": department.name, "orientation": department.orientation, "zoneId": department.zone_id, "zoneName": department.zone.name}, "createdAt": planogram.created_at, "updatedAt": planogram.updated_at, "modules": [module_entity(module) for module in planogram.modules.all().order_by("sequence", "id")]}
    if availability:
        result.pop("departmentId")
        result.pop("department")
        for module in result["modules"]:
            module["isAvailable"] = True
    if branches_count is not None:
        result["branchesCount"] = branches_count
    return result


def load_planogram(pk):
    return Planogram.objects.select_related("department__zone").prefetch_related("modules__shelves__levels__level").get(pk=pk)


def load_module(pk):
    return Module.objects.prefetch_related("shelves__levels__level").get(pk=pk)


def load_shelf(pk):
    return Shelf.objects.prefetch_related("levels__level").get(pk=pk)


def validate_create(data):
    if not isinstance(data, dict) or not valid_int(data.get("departmentId"), positive=True) or not valid_int(data.get("maxModuleWidth"), positive=True): return False
    if "name" in data and not isinstance(data["name"], str): return False
    modules = data.get("modules")
    if not isinstance(modules, list) or not modules: return False
    for module in modules:
        if not isinstance(module, dict) or not valid_int(module.get("sequence"), positive=True) or not isinstance(module.get("shelves"), list) or not module["shelves"]: return False
        for shelf in module["shelves"]:
            if not isinstance(shelf, dict) or not valid_int(shelf.get("sequence"), positive=True) or not isinstance(shelf.get("levels"), list) or not shelf["levels"]: return False
            for item in shelf["levels"]:
                if not isinstance(item, dict) or not valid_int(item.get("levelId"), positive=True) or not valid_int(item.get("width"), positive=True) or not valid_int(item.get("sequence"), positive=True) or item.get("expositionType") not in EXPOSITION_TYPES: return False
    return True


class PlanogramBase(AuthenticatedController):
    authorized_roles = ("ADMIN",)


class PlanogramView(PlanogramBase):
    def post(self, request):
        if not validate_create(request.data):
            message = "ID do departamento é obrigatório, Comprimento do módulo é obrigatório, Os módulos são obrigatórios" if request.data == {} else "Erro de validação"
            return self.bad_request({"name": "InputValidationError", "message": message})
        data = request.data
        try: planogram = PlanogramService().create(department_id=data["departmentId"], name=data.get("name"), max_module_width=data["maxModuleWidth"], modules=data["modules"])
        except LevelsNotFound as exc: return error(self, "not_found", exc)
        except (ModuleSequenceConflict, ShelfSequenceConflict, ShelfLevelSequenceConflict, PlanogramDepartmentConflict, MaxShelfWidthExceeded) as exc: return error(self, "conflict", exc)
        if not planogram: return self.not_found({"name": "DepartmentNotFoundError", "message": f"Departamento com ID {data['departmentId']} não foi encontrado."})
        return self.created(planogram_entity(load_planogram(planogram.pk)))


class ModuleView(PlanogramBase):
    def post(self, request):
        data = request.data
        if not isinstance(data, dict) or not valid_int(data.get("planogramId"), positive=True) or not valid_int(data.get("width"), positive=True): return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        planogram = PlanogramService().create_module(data["planogramId"], data["width"])
        if not planogram: return self.not_found({"name": "PlanogramNotFound", "message": f"O planogram com ID {data['planogramId']} não foi encontrado."})
        return self.created(planogram_entity(load_planogram(planogram.pk)))


class ShelfView(PlanogramBase):
    def post(self, request):
        data = request.data
        if not isinstance(data, dict) or not valid_int(data.get("moduleId"), positive=True): return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        try: module = PlanogramService().create_shelf(data["moduleId"])
        except ModuleNotFound as exc: return error(self, "not_found", exc)
        return self.created(module_entity(load_module(module.pk)))


class ShelfLevelView(PlanogramBase):
    def post(self, request):
        data = request.data; item = data.get("shelfLevel") if isinstance(data, dict) else None
        if not isinstance(item, dict) or not valid_int(data.get("shelfId"), positive=True) or not valid_int(item.get("levelId"), positive=True) or not valid_int(item.get("width"), positive=True) or item.get("expositionType") not in EXPOSITION_TYPES: return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        try: shelf = PlanogramService().add_shelf_level(data["shelfId"], item["levelId"], item["width"], item["expositionType"])
        except (ShelfNotFound, LevelsNotFound) as exc: return error(self, "not_found", exc)
        except (PlanogramDepartmentConflict, MaxShelfWidthExceeded) as exc: return error(self, "conflict", exc)
        return self.ok(shelf_entity(load_shelf(shelf.pk)))


class DeleteModuleView(PlanogramBase):
    def delete(self, request, module_id):
        try: planogram = PlanogramService().delete_module(int(module_id))
        except ModuleNotFound as exc: return error(self, "not_found", exc)
        except ShelfExistanceConflict as exc: return error(self, "conflict", exc)
        return self.ok(planogram_entity(load_planogram(planogram.pk)))


class DeleteShelfView(PlanogramBase):
    def delete(self, request, shelf_id):
        try: module = PlanogramService().delete_shelf(int(shelf_id))
        except ShelfNotFound as exc: return error(self, "not_found", exc)
        except ShelfLevelExistanceConflict as exc: return error(self, "conflict", exc)
        return self.ok(module_entity(load_module(module.pk)))


class DeleteShelfLevelView(PlanogramBase):
    def delete(self, request, id):
        shelf = PlanogramService().delete_shelf_level(int(id))
        if not shelf: return self.not_found({"name": "ShelfLevelNotFound", "message": f"Nível da prateleira com id {id} não foi encontrado."})
        return self.ok(shelf_entity(load_shelf(shelf.pk)))


class SequenceView(PlanogramBase):
    method = None; response = None
    def patch(self, request):
        data = request.data; id_key = {"module": "moduleId", "shelf": "shelfId", "shelf_level": "shelfLevelId"}[self.method]
        if not isinstance(data, dict) or not valid_int(data.get(id_key)) or not valid_int(data.get("sequence")): return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        try: result = getattr(PlanogramService(), f"update_{self.method}_sequence")(data[id_key], data["sequence"])
        except (ModuleNotFound, ShelfNotFound, ShelfLevelNotFound) as exc: return error(self, "not_found", exc)
        if self.response == "planogram": return self.ok(planogram_entity(load_planogram(result.pk)))
        if self.response == "module": return self.ok(module_entity(load_module(result.pk)))
        return self.ok(shelf_entity(load_shelf(result.pk)))


class UpdateModuleSequenceView(SequenceView): method, response = "module", "planogram"
class UpdateShelfSequenceView(SequenceView): method, response = "shelf", "module"
class UpdateShelfLevelSequenceView(SequenceView): method, response = "shelf_level", "shelf"


class UpdateShelfLevelView(PlanogramBase):
    def put(self, request):
        data = request.data
        if not isinstance(data, dict) or not valid_int(data.get("id"), positive=True) or ("width" not in data and "expositionType" not in data) or ("width" in data and not valid_int(data["width"], positive=True)) or ("expositionType" in data and data["expositionType"] not in EXPOSITION_TYPES): return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        try: item = PlanogramService().update_shelf_level(data["id"], data.get("width"), data.get("expositionType"))
        except ShelfLevelNotFound as exc: return error(self, "not_found", exc)
        except MaxShelfWidthExceeded as exc: return error(self, "conflict", exc)
        return self.ok(level_entity(item))


class UpdatePlanogramNameView(PlanogramBase):
    def patch(self, request):
        data = request.data
        if not isinstance(data, dict) or not valid_int(data.get("planogramId"), positive=True) or not isinstance(data.get("name"), str): return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        if not PlanogramService().update_planogram_name(data["planogramId"], data["name"]): return self.not_found({"name": "PlanogramNotFound", "message": f"O planogram com ID {data['planogramId']} não foi encontrado."})
        return self.ok()


class UpdatePlanogramStatusView(PlanogramBase):
    def patch(self, request, id):
        data = request.data
        if not isinstance(data, dict) or not isinstance(data.get("isActive"), bool): return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        planogram = PlanogramService().update_planogram_status(int(id), data["isActive"])
        # A ausência neste fluxo mantém a resposta de erro interno definida pelo contrato.
        if not planogram: return self.internal_server_error({"name": "PlanogramNotFound", "message": f"O planogram com ID {id} não foi encontrado."})
        return self.ok(planogram_entity(load_planogram(planogram.pk)))


class ListPlanogramsView(PlanogramBase):
    def get(self, request):
        query = Planogram.objects.select_related("department__zone").prefetch_related("modules__shelves__levels__level")
        text = request.query_params.get("queryString"); active = request.query_params.get("isActive")
        if active in ("true", "false"): query = query.filter(is_active=active == "true")
        if text:
            condition = Q(name__icontains=text) | Q(department__name__icontains=text)
            if text.isdigit(): condition |= Q(pk=int(text))
            query = query.filter(condition)
        try: page_size, page_number = int(request.query_params.get("pageSize", 10)), int(request.query_params.get("pageNumber", 1))
        except ValueError: return self.bad_request({"name": "InputValidationError", "message": "Tipo inválido para o campo pageSize"})
        total = query.count(); rows = query.order_by("id")[(page_number - 1) * page_size:page_number * page_size]
        return self.ok({"totalPages": -(-total // page_size), "results": [planogram_entity(row, branches_count=0) for row in rows]})


class GetPlanogramsByDepartmentView(PlanogramBase):
    def get(self, request):
        raw = request.query_params.get("departmentId")
        if not raw or not raw.isdigit(): return self.bad_request({"name": "InputValidationError", "message": "O id do departamento é obrigatório."})
        rows = Planogram.objects.filter(department_id=int(raw)).select_related("department__zone").prefetch_related("modules__shelves__levels__level").order_by("id")
        return self.ok({"results": [planogram_entity(row, branches_count=0, availability=True) for row in rows]})


class GetPlanogramView(AuthenticatedController):
    def get(self, request):
        raw = request.query_params.get("planogramId")
        if not raw or not raw.isdigit() or int(raw) < 1:
            return self.bad_request({"name": "InputValidationError", "message": "Tipo inválido para ID do planograma"})
        branch_raw = request.query_params.get("branchId")
        if branch_raw is not None and (not branch_raw.isdigit() or int(branch_raw) < 1):
            return self.bad_request({"name": "InputValidationError", "message": "Tipo inválido para ID da filial"})
        element_raw = request.query_params.get("layoutElementId")
        if element_raw is not None and (not element_raw.isdigit() or int(element_raw) < 1):
            return self.bad_request({"name": "InputValidationError", "message": "Tipo inválido para ID do elemento de layout"})
        branch_id = int(branch_raw) if branch_raw else None
        value, problem = mount(int(raw), branch_id, request.query_params.get("checkStock") == "true", int(element_raw) if element_raw else None)
        if problem == "planogram": return self.not_found({"name": "PlanogramNotFound", "message": f"O planogram com ID {raw} não foi encontrado."})
        if problem == "layout": return self.not_found({"name": "BranchLayoutNotFound", "message": f"Layout da loja com id {branch_id} não foi encontrado."})
        if problem == "modules": return self.unprocessable_entity({"name": "BranchWithoutPlanogramModules", "message": "A filial não possui módulos associados a este planograma."})
        if problem == "marketing": return self.bad_request({"name": "MarketingPlanogramElementConflict", "message": "É necessário informar o ID do elemento de layout para planogramas de setores de ponto de marketing"})
        return self.ok(value)


class GetPlanogramMetricsView(PlanogramBase):
    def get(self, request, planogram_id):
        if not planogram_id.isdigit() or int(planogram_id) < 1:
            return self.bad_request({"name": "InputValidationError", "message": "Tipo inválido para ID do planograma"})
        value, problem = mount(int(planogram_id))
        if problem == "planogram": return self.not_found({"name": "PlanogramNotFound", "message": f"O planogram com ID {planogram_id} não foi encontrado."})
        levels = value["levelsProductsExpositionMap"]
        total = sum(item["totalWidth"] for item in levels.values())
        metrics = []
        for item in sorted(levels.values(), key=lambda row: row["levelName"]):
            exposed_width = round(sum((product["width"] if product["expositionDetails"]["fixedSide"] == "WIDTH" else product["height"] if product["expositionDetails"]["fixedSide"] == "HEIGHT" else product.get("length") or product["width"]) for product in item["exposedProducts"]), 2)
            all_width = round(exposed_width + sum((product["width"] if product["expositionDetails"]["fixedSide"] == "WIDTH" else product["height"] if product["expositionDetails"]["fixedSide"] == "HEIGHT" else product.get("length") or product["width"]) for product in item["nonExposedProducts"]), 2)
            metrics.append({"levelName": item["levelName"], "totalSkusExposed": len({product["id"] for product in item["exposedProducts"]}), "totalWidth": item["totalWidth"], "totalWidthExposed": exposed_width, "totalWidthToExposeAllProducts": all_width, "relativeWidthPercentage": round((item["totalWidth"] / total) * 100, 2) if total else 0})
        return self.ok({"levelsExpositionMetrics": metrics})
