from src.middlewares.auth import AuthenticatedController
from .factory import build_use_case
from .use_case import DeleteBranchUseCase
class DeleteBranchView(AuthenticatedController):
    authorized_roles = ("ADMIN",)
    def delete(self, request, branch_id): return self.respond(build_use_case().run(DeleteBranchUseCase.parse(branch_id)), {"InputValidationError": 400, "BranchNotFoundError": 404})
