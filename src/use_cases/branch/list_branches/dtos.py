import math
from dataclasses import dataclass

from src.core.compatibility import js_number, js_truthy, query_value


@dataclass
class ListBranchesInput:
    filters: dict
    page_number: float
    page_size: float
    role: str
    allowed_ids: list | None

    @classmethod
    def from_request(cls, request):
        def pagination(key, default):
            value = query_value(request.query_params, key)
            return js_number(value if js_truthy(value) else default)
        return cls(
            filters={key: query_value(request.query_params, key) for key in ("queryString", "ufs")},
            page_number=pagination("pageNumber", 1), page_size=pagination("pageSize", 10),
            role=request.token_claims["role"], allowed_ids=request.token_claims.get("allowedBranchesIds"),
        )

    def validation_errors(self):
        errors = []
        for field, expected, message in [
            ("queryString", str, "Tipo inválido para campo queryString"),
            ("ufs", list, "Tipo inválido para campo uf"),
        ]:
            value = self.filters.get(field)
            if value is not None and not isinstance(value, expected):
                errors.append(message)
        for field, value in [("pageNumber", self.page_number), ("pageSize", self.page_size)]:
            if math.isnan(value):
                errors.append(f"Tipo inválido para o campo {field}")
        return errors
