from src.core.either import right, wrong
from src.core.use_case import UseCase
from src.entities.user.errors import UserBlocked
from src.errors import InputValidationError
from src.services.token.service import TokenType

from .dtos import validation_errors


class RefreshTokenUseCase(UseCase):
    def __init__(self, user_service, token_service):
        self.user_service = user_service
        self.token_service = token_service

    def validate(self, data):
        errors = validation_errors(data)
        return wrong(InputValidationError(", ".join(errors))) if errors else right(None)

    def execute(self, data):
        verified = self.token_service.verify(data["refreshToken"], TokenType.RefreshToken)
        if verified.is_wrong():
            return wrong(verified.value)
        result = self.user_service.get_user(verified.value.get("sub"))
        if result.is_wrong():
            return wrong(result.value)
        user = result.value
        if not user.is_active:
            return wrong(UserBlocked())
        branches = self.user_service.get_user_branches_ids(user.id)
        claims = {"sub": user.id, "email": user.email}
        # A renovação exige somente que o usuário esteja ativo.
        if user.role:
            claims["role"] = user.role
        if branches:
            claims["allowedBranchesIds"] = branches
        access = self.token_service.sign(TokenType.AccessToken, claims)
        return right({"accessToken": access.token, "expiresAt": access.expires_at})
