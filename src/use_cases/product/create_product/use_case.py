from src.core import UseCase
from src.core.either import Either, right, wrong
from src.errors import InputValidationError, ApplicationError, BusinessError, UnknownError, ConflictError
from .dtos import CreateProductInput, CreateProductOutput

Input = CreateProductInput
FailureOutput = BusinessError | ApplicationError | UnknownError
SuccessOutput = CreateProductOutput


class CreateProductUseCase(UseCase):
    def __init__(self, repository):
        self.repository = repository

    def validate(self, input_data: Input) -> Either:
        if not input_data.ean:
            return wrong(InputValidationError("ean é obrigatório"))
        if not input_data.name:
            return wrong(InputValidationError("name é obrigatório"))
        if input_data.width <= 0 or input_data.height <= 0 or input_data.length <= 0:
            return wrong(InputValidationError("width, height e length devem ser maiores que zero"))
        return right(None)

    def execute(self, input_data: Input) -> Either:
        try:
            existing = self.repository.find_by_ean(input_data.ean)
            if existing:
                return wrong(ConflictError(f"Product com ean '{input_data.ean}' já existe"))

            product = self.repository.create(
                ean=input_data.ean,
                name=input_data.name,
                width=input_data.width,
                height=input_data.height,
                length=input_data.length,
                is_active=input_data.is_active,
            )
            return right(CreateProductOutput(id=product.id, ean=product.ean, name=product.name))
        except Exception as e:
            return wrong(UnknownError(str(e)))
