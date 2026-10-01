import math
from src.core.compatibility import js_number
from src.middlewares.auth import AuthenticatedController
from src.entities.zone.service import ZoneService

ERRORS = {"ZoneNameConflict": 409, "ZoneNotFoundError": 404, "ZoneWithDepartmentsConflict": 409, "DepartmentNameConflict": 409, "DepartmentNotFoundError": 404, "DepartmentWithLevelsConflict": 409, "LevelNameConflict": 409, "LevelNotFound": 404}

class ZoneView(AuthenticatedController):
    authorized_roles = ("ADMIN",)
    def get(self, request): return self.ok(ZoneService().list_zones())
    def post(self, request):
        data = request.data
        if not isinstance(data, dict) or not isinstance(data.get("name"), str) or not isinstance(data.get("hexColor"), str): return self.bad_request({"name":"InputValidationError","message":"Erro de validação"})
        result = ZoneService().create_zone(data)
        return self.created(result.value) if not result.is_wrong() else self.respond(result, ERRORS)
    def put(self, request): return self.respond(ZoneService().update_zone(request.data), ERRORS)

class DepartmentView(AuthenticatedController):
    authorized_roles = ("ADMIN",)
    def get(self, request): return self.ok(ZoneService().list_departments())
    def post(self, request):
        data = request.data
        if not isinstance(data, dict) or not isinstance(data.get("name"), str) or data.get("orientation") not in ("ENTRY","COUNTER","LEFT_TO_RIGHT"): return self.bad_request({"name":"InputValidationError","message":"Erro de validação"})
        return self.respond(ZoneService().create_department(data), ERRORS)
    def put(self, request): return self.respond(ZoneService().update_department(request.data), ERRORS)

class LevelView(AuthenticatedController):
    authorized_roles = ("ADMIN",)
    def get(self, request, department_id): return self.ok(ZoneService().list_levels(int(js_number(department_id))))
    def post(self, request):
        data = request.data
        if not isinstance(data, dict) or not isinstance(data.get("name"), str) or not isinstance(data.get("hexColor"), str) or not isinstance(data.get("divisions"), list): return self.bad_request({"name":"InputValidationError","message":"Erro de validação"})
        result = ZoneService().create_level(data)
        return self.created(result.value) if not result.is_wrong() else self.respond(result, ERRORS)
    def put(self, request): return self.respond(ZoneService().update_level(request.data), ERRORS)

class DeleteView(AuthenticatedController):
    authorized_roles = ("ADMIN",)
    operation = None
    def delete(self, request, object_id):
        value = js_number(object_id)
        if not math.isfinite(value): return self.bad_request({"name":"InputValidationError","message":"Erro de validação"})
        result = getattr(ZoneService(), self.operation)(int(value) if value.is_integer() else value)
        return self.no_content() if not result.is_wrong() else self.respond(result, ERRORS)
class DeleteZoneView(DeleteView): operation="delete_zone"
class DeleteDepartmentView(DeleteView): operation="delete_department"
class DeleteLevelView(DeleteView): operation="delete_level"
