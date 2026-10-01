from src.middlewares.auth import AuthenticatedController
from .dtos import parse_id
from .factory import build_use_case


class GetBranchView(AuthenticatedController):
    def get(self, request, branch_id):
        return self.respond(build_use_case().run(parse_id(branch_id)),
                            {"InputValidationError": 400, "BranchNotFoundError": 404})
