from src.core.compatibility import CompatibilityController
from .factory import build_use_case


class RegisterView(CompatibilityController):
    def post(self, request):
        result = build_use_case().run(request.data)
        if result.is_wrong():
            return self.respond(result, {"InputValidationError": 400,
                                         "UserEmailAlreadyExists": 409,
                                         "UserItecAlreadyExists": 409})
        return self.created()
