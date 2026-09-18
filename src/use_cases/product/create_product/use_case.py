from src.core import UseCase
from src.core.either import Either, right, wrong
from src.entities.product.errors import DuplicateProductEanError
from src.errors import InputValidationError, ApplicationError, BusinessError, UnknownError
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
        for field in ("width", "height", "length"):
            value = getattr(input_data, field)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return wrong(InputValidationError(f"{field} é obrigatório e deve ser numérico"))
            if value <= 0:
                return wrong(InputValidationError(f"{field} deve ser maior que zero"))
        return right(None)

    def execute(self, input_data: Input) -> Either:
        try:
            # Sem checar find_by_ean antes: entre a checagem e o insert outra
            # requisição pode criar o mesmo EAN. O unique do banco é a fonte de verdade.
            product = self.repository.create(
                ean=input_data.ean,
                name=input_data.name,
                width=input_data.width,
                height=input_data.height,
                length=input_data.length,
                is_active=input_data.is_active,
            )
            return right(CreateProductOutput(id=product.id, ean=product.ean, name=product.name))
        except DuplicateProductEanError as e:
            return wrong(e)
