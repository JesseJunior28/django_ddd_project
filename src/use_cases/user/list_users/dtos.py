import math
from dataclasses import dataclass
from src.core.compatibility import js_number, js_truthy, query_value


@dataclass
class ListUsersInput:
    filters: dict
    page_number: float
    page_size: float

    @classmethod
    def from_request(cls, request):
        query = request.query_params
        active = query_value(query, "isActive")
        def page(key, default):
            value = query_value(query, key)
            return js_number(value if js_truthy(value) else default)
        return cls({"queryString": query_value(query, "queryString"),
                    "roles": query_value(query, "roles"),
                    "isActive": True if active == "true" else False if active == "false" else None},
                   page("pageNumber", 1), page("pageSize", 10))

    def validation_errors(self):
        errors = []
        for key, kind in [("queryString", str), ("roles", list)]:
            value = self.filters.get(key)
            if value is not None and not isinstance(value, kind):
                errors.append(f"Tipo inválido para o campo {key}")
        for key, value in [("pageNumber", self.page_number), ("pageSize", self.page_size)]:
            if math.isnan(value):
                errors.append(f"Tipo inválido para o campo {key}")
        return errors
