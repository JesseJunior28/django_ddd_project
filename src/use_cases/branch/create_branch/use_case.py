from src.core.either import right, wrong
from src.core.use_case import UseCase
from src.errors import InputValidationError

from .dtos import validation_errors


class CreateBranchUseCase(UseCase):
    def __init__(self, service):
        self.service = service

    def validate(self, data):
        errors = validation_errors(data)
        return wrong(InputValidationError(", ".join(errors))) if errors else right(None)

    def execute(self, data):
        # O serviço recebe o payload integral para aplicar suas próprias validações.
        return self.service.create_branch(dict(data))
