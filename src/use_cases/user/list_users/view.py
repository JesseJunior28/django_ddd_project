from src.middlewares.auth import AuthenticatedController
from .dtos import ListUsersInput
from .factory import build_use_case


class ListUsersView(AuthenticatedController):
    authorized_roles = ("ADMIN",)

    def get(self, request):
        return self.respond(build_use_case().run(ListUsersInput.from_request(request)),
                            {"InputValidationError": 400})
