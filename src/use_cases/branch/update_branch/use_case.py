from src.core.either import right, wrong
from src.core.use_case import UseCase
from src.errors import InputValidationError
from .dtos import validation_errors
class UpdateBranchUseCase(UseCase):
    def __init__(self, service): self.service = service
    def validate(self, data):
        errors = validation_errors(data)
        return wrong(InputValidationError(", ".join(errors))) if errors else right(None)
    def execute(self, data):
        # Campos desconhecidos chegam ao serviço para que a escrita seja rejeitada,
        # em vez de serem descartados silenciosamente.
        fields = {key: value for key, value in data.items() if key != "id"}
        return self.service.update_branch(data["id"], fields)
