from src.core.either import right, wrong
from src.core.use_case import UseCase
from src.errors import InputValidationError
from .dtos import validation_errors


class ResetPasswordUseCase(UseCase):
    def __init__(self, service, token_service):
        self.service = service
        self.token_service = token_service

    def validate(self, data):
        errors = validation_errors(data)
        return wrong(InputValidationError(", ".join(errors))) if errors else right(None)

    def execute(self, data):
        token = self.token_service.verify(data["token"])
        if token.is_wrong():
            return wrong(token.value)
        verified = self.service.verify_reset_token(token.value.get("sub"), data["token"])
        if verified.is_wrong():
            return verified
        return self.service.reset_password(token.value.get("sub"), data["password"], verified.value)
