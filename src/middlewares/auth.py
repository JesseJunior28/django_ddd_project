from src.core.compatibility import (
    CompatibilityController, HttpContractError, js_number, js_truthy, query_value,
)
from src.entities.user.models import UserRoles
from src.services.token.jwt_implementation import JwtTokenService


class AuthenticatedController(CompatibilityController):
    authorized_roles = tuple(UserRoles.values)

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HttpContractError(401, "MiddlewareTokenError", "Token was not provided.")
        if not authorization.startswith("Bearer "):
            raise HttpContractError(401, "MiddlewareTokenError", "Token has invalid format.")
        token = authorization.split(" ")[1]
        result = JwtTokenService().verify(token)
        if result.is_wrong():
            raise HttpContractError(401, "MiddlewareTokenError", str(result.value))
        claims = result.value
        if claims.get("role") not in self.authorized_roles:
            raise HttpContractError(403, "NotEnoughPermsTokenError",
                                    "Usuário sem acesso suficiente para o recurso.")
        branch_id = query_value(request.query_params, "branchId")
        if not js_truthy(branch_id):
            branch_id = kwargs.get("branchId")
        if not js_truthy(branch_id) and isinstance(request.data, dict):
            branch_id = request.data.get("branchId")
        if js_truthy(branch_id) and claims.get("role") not in ("ADMIN", "BACKOFFICE", "LAYOUT"):
            allowed = claims.get("allowedBranchesIds") or []
            number = js_number(branch_id)
            if not isinstance(allowed, list) or not any(
                type(item) in (int, float) and item == number for item in allowed
            ):
                raise HttpContractError(403, "UnauthorizedBranchError",
                                        "Usuário sem acesso para a loja requisitada.")
        request.token_claims = claims
