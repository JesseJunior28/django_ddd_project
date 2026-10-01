from src.entities.user.service import UserService
from .use_case import GetUserUseCase


def build_use_case():
    return GetUserUseCase(UserService())
