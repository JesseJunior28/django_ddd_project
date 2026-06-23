from rest_framework.request import Request
from rest_framework.response import Response

from src.core import Controller
from src.errors import InputValidationError, UnknownError, ConflictError
from .dtos import CreateProductInput
from .factory import build_use_case


class CreateProductView(Controller):
    def post(self, request: Request) -> Response:
        use_case = build_use_case()

        input_data = CreateProductInput(
            ean=request.data.get("ean"),
            name=request.data.get("name"),
            width=request.data.get("width"),
            height=request.data.get("height"),
            length=request.data.get("length"),
            is_active=request.data.get("is_active", True),
        )

        result = use_case.run(input_data)

        if result.is_wrong():
            error = result.value
            return self.map_error(error, {
                InputValidationError: self.bad_request,
                ConflictError: self.bad_request,
                UnknownError: self.internal_server_error,
            })

        return self.created({
            "id": result.value.id,
            "ean": result.value.ean,
            "name": result.value.name,
        })
