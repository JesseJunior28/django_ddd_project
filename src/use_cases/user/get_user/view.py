from src.middlewares.auth import AuthenticatedController
from .dtos import GetUserInput
from .factory import build_use_case


class GetUserView(AuthenticatedController):
    def get(self, request):
        return self.respond(build_use_case().run(GetUserInput(request.token_claims.get("sub"))),
                            {"InputValidationError": 400, "UserNotFound": 404})
