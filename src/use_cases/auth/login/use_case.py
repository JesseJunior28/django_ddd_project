from src.core.use_case import UseCase
from src.core.either import right, wrong
from src.errors import InputValidationError
from .dtos import validation_errors


class LoginUseCase(UseCase):
    def __init__(self, user_service):
        self.user_service = user_service

    def validate(self, data):
        errors = validation_errors(data)
        return wrong(InputValidationError(", ".join(errors))) if errors else right(None)

    def execute(self, data):
        return self.user_service.validate_credentials(data)
