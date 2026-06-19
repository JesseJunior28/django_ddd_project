from src.core import UseCase
from src.core.either import Either, right, wrong
from src.errors import InputValidationError, ApplicationError, BusinessError, UnknownError
from .dtos import CreateBranchInput, CreateBranchOutput

Input = CreateBranchInput
FailureOutput = BusinessError | ApplicationError | UnknownError
SuccessOutput = CreateBranchOutput


class CreateBranchUseCase(UseCase):
    def __init__(self, repository):
        self.repository = repository

    def validate(self, input_data: Input) -> Either:
        if not input_data.name:
            return wrong(InputValidationError("name é obrigatório"))
        if not input_data.industry_id:
            return wrong(InputValidationError("industry_id é obrigatório"))
        return right(None)

    def execute(self, input_data: Input) -> Either:
        try:
            branch = self.repository.create(
                name=input_data.name,
                industry_id=input_data.industry_id,
            )
            return right(CreateBranchOutput(id=str(branch.id), name=branch.name))
        except Exception as e:
            return wrong(UnknownError(str(e)))
