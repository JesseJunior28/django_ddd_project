from django.apps import AppConfig


class AppConfig_(AppConfig):
    """
    App "técnico" — não tem models, existe só para o Django
    reconhecer os management commands (ex: make_usecase).
    Agrupa comandos de manutenção e componentes técnicos do projeto.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "src._app"
    label = "tooling"

    def ready(self):
        from . import checks  # noqa: F401 — registra os system checks
