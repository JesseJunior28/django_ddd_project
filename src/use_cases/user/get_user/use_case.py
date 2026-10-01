from src.core.either import right, wrong
from src.core.use_case import UseCase
from src.errors import InputValidationError


class GetUserUseCase(UseCase):
    def __init__(self, service):
        self.service = service

    def validate(self, data):
        return right(None) if data else wrong(InputValidationError())

    def execute(self, data):
        result = self.service.get_user(data.user_id)
        return wrong(result.value) if result.is_wrong() else right(self.service.map_to_entity(result.value))
