from src.core.either import right, wrong
from src.core.use_case import UseCase
from src.errors import InputValidationError
from src.errors.domain_errors import PersistenceError
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from .dtos import validation_errors


class RegisterUseCase(UseCase):
    def __init__(self, service):
        self.service = service

    def validate(self, data):
        errors = validation_errors(data)
        return wrong(InputValidationError(", ".join(errors))) if errors else right(None)

    def execute(self, data):
        try:
            result = self.service.create_user(data)
            return result if result.is_wrong() else right(None)
        except (ValidationError, DatabaseError):
            return wrong(PersistenceError())
