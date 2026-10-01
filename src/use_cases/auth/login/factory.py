from src.entities.user.service import UserService
from .use_case import LoginUseCase


def build_use_case():
    return LoginUseCase(UserService())
