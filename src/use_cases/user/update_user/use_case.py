from src.core.either import right, wrong
from src.core.use_case import UseCase
from src.errors import InputValidationError
from src.errors.domain_errors import PersistenceError
from django.core.exceptions import ValidationError
from django.db import DatabaseError, transaction
from .dtos import validation_errors


class UpdateUserUseCase(UseCase):
    def __init__(self, service):
        self.service = service

    def validate(self, data):
        errors = validation_errors(data)
        return wrong(InputValidationError(", ".join(errors))) if errors else right(None)

    def execute(self, data):
        try:
            with transaction.atomic():
                return self.service.update_user(data)
        except (ValidationError, DatabaseError):
            return wrong(PersistenceError())
