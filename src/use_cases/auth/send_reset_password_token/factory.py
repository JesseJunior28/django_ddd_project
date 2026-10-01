from src.entities.user.service import UserService
from src.services.email.smtp_implementation import SmtpEmailService
from .use_case import SendResetPasswordTokenUseCase


def build_use_case():
    return SendResetPasswordTokenUseCase(UserService(), SmtpEmailService())
