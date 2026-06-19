from rest_framework.request import Request
from rest_framework.response import Response

from src.core import Controller
from src.errors import InputValidationError, UnknownError
from .dtos import CreateBranchInput
from .factory import build_use_case


class CreateBranchView(Controller):
    def post(self, request: Request) -> Response:
        use_case = build_use_case()

        input_data = CreateBranchInput(
            name=request.data.get("name"),
            industry_id=request.data.get("industry_id"),
        )

        result = use_case.run(input_data)

        if result.is_wrong():
            error = result.value
            return self.map_error(error, {
                InputValidationError: self.bad_request,
                UnknownError: self.internal_server_error,
            })

        return self.created({"id": result.value.id, "name": result.value.name})
