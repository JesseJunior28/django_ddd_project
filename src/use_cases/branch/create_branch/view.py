from rest_framework.response import Response

from src.entities.branch.repository import BranchRepository
from src.middlewares.auth import AuthenticatedController
from .factory import build_use_case


class CreateBranchView(AuthenticatedController):
    authorized_roles = ("ADMIN",)

    def post(self, request):
        return self.respond(build_use_case().run(request.data), {"InputValidationError": 400})


class LegacyCreateBranchView(AuthenticatedController):
    """Endpoint legado de criação de filial."""

    authorized_roles = ("ADMIN",)

    def post(self, request):
        fields = ("name", "city", "uf", "address")
        if any(not request.data.get(field) for field in fields):
            return Response({"error": "InputValidationError"}, status=400)
        branch = BranchRepository().create(**{field: request.data[field] for field in fields})
        return Response({"id": branch.id, "name": branch.name}, status=201)
