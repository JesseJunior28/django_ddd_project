from src.entities.user.service import UserService
from .use_case import UpdateUserUseCase


def build_use_case():
    return UpdateUserUseCase(UserService())
