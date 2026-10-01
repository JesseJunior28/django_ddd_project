from src.core.compatibility import CompatibilityController
from .factory import build_use_case


class SendResetPasswordTokenView(CompatibilityController):
    def post(self, request):
        return self.respond(build_use_case().run(request.data), {
            "InputValidationError": 400, "UserNotFound": 404, "UserBlocked": 401,
        })
