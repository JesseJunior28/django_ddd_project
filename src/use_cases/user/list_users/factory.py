from src.entities.user.service import UserService
from .use_case import ListUsersUseCase


def build_use_case():
    return ListUsersUseCase(UserService())
