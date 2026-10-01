from src.core.either import right, wrong
from src.core.use_case import UseCase
from src.errors import InputValidationError
from .dtos import validation_errors


class SendResetPasswordTokenUseCase(UseCase):
    def __init__(self, service, email_service):
        self.service = service
        self.email_service = email_service

    def validate(self, data):
        errors = validation_errors(data)
        return wrong(InputValidationError(", ".join(errors))) if errors else right(None)

    def execute(self, data):
        result = self.service.get_reset_password_data(data["email"])
        if result.is_wrong():
            return result
        self.email_service.send_reset_password(**result.value)
        return right(None)
