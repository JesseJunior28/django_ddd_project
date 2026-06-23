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
        if not input_data.city:
            return wrong(InputValidationError("city é obrigatório"))
        if not input_data.uf or len(input_data.uf) != 2:
            return wrong(InputValidationError("uf é obrigatório e deve ter 2 caracteres"))
        if not input_data.address:
            return wrong(InputValidationError("address é obrigatório"))
        return right(None)

    def execute(self, input_data: Input) -> Either:
        try:
            branch = self.repository.create(
                name=input_data.name,
                city=input_data.city,
                uf=input_data.uf,
                address=input_data.address,
            )
            return right(CreateBranchOutput(id=branch.id, name=branch.name))
        except Exception as e:
            return wrong(UnknownError(str(e)))
