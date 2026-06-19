from django.apps import AppConfig


class AppConfig_(AppConfig):
    """
    App "técnico" — não tem models, existe só para o Django
    reconhecer os management commands (ex: make_usecase).
    Equivalente a uma pasta de scripts/tooling no projeto TS.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "src._app"
    label = "tooling"
