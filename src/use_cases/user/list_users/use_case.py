import math
from src.core.either import right, wrong
from src.core.use_case import UseCase
from src.errors import InputValidationError


class ListUsersUseCase(UseCase):
    def __init__(self, service):
        self.service = service

    def validate(self, data):
        errors = data.validation_errors()
        return wrong(InputValidationError(", ".join(errors))) if errors else right(None)

    def execute(self, data):
        query = self.service.repository.filtered(data.filters)
        results = self.service.get_users(query, data.page_size, data.page_number)
        count = self.service.repository.count_users(query)
        pages = math.ceil(count / data.page_size) if data.page_size else None
        return right({"totalPages": pages, "results": results})
