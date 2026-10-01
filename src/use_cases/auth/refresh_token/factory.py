from src.entities.user.service import UserService
from src.services.token.jwt_implementation import JwtTokenService

from .use_case import RefreshTokenUseCase


def build_use_case():
    return RefreshTokenUseCase(UserService(), JwtTokenService())
