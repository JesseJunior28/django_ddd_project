from src.core.either import right, wrong
from src.core.use_case import UseCase
from src.errors import InputValidationError
from .dtos import validation_errors


class GetBranchUseCase(UseCase):
    def __init__(self, service):
        self.service = service

    def validate(self, branch_id):
        errors = validation_errors(branch_id)
        return wrong(InputValidationError(", ".join(errors))) if errors else right(None)

    def execute(self, branch_id):
        return self.service.get_branch_by_id(branch_id)
