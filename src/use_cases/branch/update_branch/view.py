from src.middlewares.auth import AuthenticatedController
from .factory import build_use_case
class UpdateBranchView(AuthenticatedController):
    authorized_roles = ("ADMIN",)
    def put(self, request): return self.respond(build_use_case().run(request.data), {"InputValidationError": 400, "BranchNotFoundError": 404})
