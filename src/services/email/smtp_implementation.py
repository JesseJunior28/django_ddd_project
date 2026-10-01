import logging
import smtplib
from email.message import EmailMessage

from django.conf import settings

logger = logging.getLogger(__name__)


class SmtpEmailService:
    """The reference swallows SMTP failures after logging them."""

    def send_reset_password(self, *, userName, userEmail, token):
        html = f'''<div style="font-family: Arial, sans-serif; line-height: 1.6;">
  <p>Olá <b>{userName}</b>,</p>
  <p>Recebemos uma solicitação para redefinir sua senha. Clique no botão abaixo para continuar:</p>
  <p style="text-align: center;"><a href="{settings.RESET_PASSWORD_PAGE_URL}?token={token}" target="_blank">Redefinir Senha</a></p>
  <p>Se você não solicitou a redefinição de senha, ignore este e-mail.</p>
  <p>Obrigado,<br/>Equipe do Suporte</p>
</div>'''
        message = EmailMessage()
        message["From"] = settings.EMAIL_SENDER
        message["To"] = userEmail
        message["Subject"] = "Gestão Espaço - Resetar Senha"
        message.set_content("Gestão Espaço - Resetar Senha")
        message.add_alternative(html, subtype="html")
        try:
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10) as client:
                if settings.EMAIL_USERNAME or settings.EMAIL_PASSWORD:
                    client.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
                client.send_message(message)
        except Exception:
            logger.exception("SmtpEmailService => send: Error ao enviar email.")
