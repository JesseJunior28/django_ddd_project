from django.conf import settings
from django.core.checks import Tags, Warning, register


@register(Tags.security)
def insecure_default_secrets(app_configs, **kwargs):
    """
    Avisa (em dev) quando os segredos padrão estão em uso.
    Com DEBUG=False o próprio settings.py já barra o boot.
    """
    defaults = {
        "DJANGO_SECRET_KEY": (settings.SECRET_KEY, settings.INSECURE_SECRET_KEY),
        "JWT_SECRET": (settings.JWT_SECRET, settings.INSECURE_JWT_SECRET),
    }
    return [
        Warning(
            f"{name} está com o valor padrão inseguro.",
            hint=f"Defina {name} no .env antes de subir para produção.",
            id="tooling.W001",
        )
        for name, (value, default) in defaults.items()
        if value == default
    ]
