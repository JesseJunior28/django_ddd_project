from src.middlewares.auth import AuthenticatedController
from .dtos import ListBranchesInput
from .factory import build_use_case


class ListBranchesView(AuthenticatedController):
    def get(self, request):
        return self.respond(build_use_case().run(ListBranchesInput.from_request(request)),
                            {"InputValidationError": 400})
