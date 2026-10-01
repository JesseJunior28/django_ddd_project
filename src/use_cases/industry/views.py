import json
import math

from src.core.compatibility import js_number, query_value
from src.errors import InputValidationError
from src.middlewares.auth import AuthenticatedController
from src.entities.industry.service import IndustryService


def validation_error(messages):
    return InputValidationError(", ".join(messages))


def create_errors(data):
    if not isinstance(data, dict):
        return ["Erro de validação desconhecido"]
    errors = []
    if data.get("name") is None:
        errors.append("Nome é obrigatório")
    elif not isinstance(data["name"], str):
        errors.append("Tipo inválido para nome da indústria")
    if "brands" not in data:
        errors.append("O campo brands é obrigatório")
    elif not isinstance(data["brands"], list):
        errors.append(f"brands must be a `array` type, but the final value was: `{json.dumps(data['brands'])}`.")
    elif any(not isinstance(value, str) for value in data["brands"]):
        errors.append("Tipo inválido para marca")
    return errors


class IndustryView(AuthenticatedController):
    authorized_roles = ("ADMIN",)
    service_class = IndustryService

    def service(self):
        return self.service_class()

    def post(self, request):
        errors = create_errors(request.data)
        if errors:
            return self.bad_request({"name": "InputValidationError", "message": str(validation_error(errors))})
        result = self.service().create_industry(request.data)
        if result.is_wrong():
            return self.respond(result, {"IndustryAlreadyExistConflict": 409})
        return self.created(result.value)

    def get(self, request):
        name = query_value(request.query_params, "industryName")
        if name is not None and not isinstance(name, str):
            return self.bad_request({"name": "InputValidationError", "message": "Tipo inválido para o nome da indústria."})
        return self.ok(self.service().list_industries(name))

    def put(self, request):
        data = request.data
        errors = []
        if not isinstance(data, dict):
            errors.append("Erro de validação desconhecido")
        else:
            if data.get("name") is None: errors.append("Nome é obrigatório")
            elif not isinstance(data["name"], str): errors.append("Tipo inválido para nome da indústria")
            if "brandsToAdd" in data and (not isinstance(data["brandsToAdd"], list) or any(not isinstance(item, str) for item in data["brandsToAdd"])):
                errors.append("Tipo inválido para marcas")
        if errors:
            return self.bad_request({"name": "InputValidationError", "message": str(validation_error(errors))})
        return self.respond(self.service().update_industry(data), {"InputValidationError": 400, "IndustryNotFoundError": 404, "IndustryAlreadyExistConflict": 409})


class DeleteIndustryView(AuthenticatedController):
    authorized_roles = ("ADMIN",)

    def delete(self, request, industry_id):
        value = js_number(industry_id)
        if not math.isfinite(value):
            return self.bad_request({"name": "InputValidationError", "message": "Tipo inválido para ID da indústria"})
        value = int(value) if value.is_integer() else value
        result = IndustryService().delete_industry(value)
        if result.is_wrong():
            return self.respond(result, {"IndustryNotFoundError": 404, "IndustryWithBrandConflict": 409})
        return self.no_content()
