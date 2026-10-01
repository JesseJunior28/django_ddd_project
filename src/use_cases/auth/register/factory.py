from src.entities.user.service import UserService
from .use_case import RegisterUseCase


def build_use_case():
    return RegisterUseCase(UserService())
