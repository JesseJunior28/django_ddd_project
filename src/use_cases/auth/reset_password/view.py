from src.core.compatibility import CompatibilityController
from .factory import build_use_case


class ResetPasswordView(CompatibilityController):
    def post(self, request):
        return self.respond(build_use_case().run(request.data), {
            "InputValidationError": 400, "UserNotFound": 404,
            "InvalidResetToken": 401, "ResetTokenExpiredError": 401,
            "InvalidTokenError": 401, "TokenExpiredError": 401,
        })
