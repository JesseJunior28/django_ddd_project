import math
from src.core.compatibility import js_number
from src.core.either import right, wrong
from src.core.use_case import UseCase
from src.errors import InputValidationError
class DeleteBranchUseCase(UseCase):
    def __init__(self, service): self.service = service
    def validate(self, data): return wrong(InputValidationError("Tipo inválido para ID da loja")) if math.isnan(data) else right(None)
    def execute(self, data): return self.service.delete_branch(data)
    @staticmethod
    def parse(value): return js_number(value)
