import math

from src.core.use_case import UseCase
from src.core.either import right, wrong
from src.errors import InputValidationError


class ListBranchesUseCase(UseCase):
    def __init__(self, branch_service):
        self.branch_service = branch_service

    def validate(self, data):
        errors = data.validation_errors()
        return wrong(InputValidationError(", ".join(errors))) if errors else right(None)

    def execute(self, data):
        query = self.branch_service.repository.filtered(data.filters, data.role, data.allowed_ids)
        results = self.branch_service.get_branches(query, data.page_size, data.page_number)
        count = self.branch_service.count_branches(query)
        pages = math.ceil(count / data.page_size) if data.page_size else None
        return right({"totalPages": pages, "results": results})
