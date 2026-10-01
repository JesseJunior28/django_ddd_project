from src.core.compatibility import CompatibilityController

from .factory import build_use_case


class RefreshTokenView(CompatibilityController):
    def post(self, request):
        return self.respond(build_use_case().run(request.data), {
            "InputValidationError": 400, "InvalidTokenError": 401,
            "TokenExpiredError": 401, "UserBlocked": 401, "UserNotFound": 404,
        })
