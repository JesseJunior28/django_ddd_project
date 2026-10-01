import os

bind = "0.0.0.0:8000"
workers = int(os.environ.get("WEB_CONCURRENCY", "1"))
# Um único processo preserva o escopo do limitador de tentativas em memória.
# Duas threads permitem sobrepor trabalho independente de banco e I/O.
worker_class = "gthread"
threads = 2
timeout = 30
graceful_timeout = 30
preload_app = False
reload = False
# O middleware registra métricas HTTP sem URLs, cabeçalhos ou corpos de requisição.
accesslog = None
errorlog = "-"
loglevel = "info"


def on_starting(server):
    if workers != 1:
        raise RuntimeError("Reference login rate limit requires one worker (in-memory counters)")
    if os.environ.get("DJANGO_DEBUG", "False") != "False":
        raise RuntimeError("Production runner requires DJANGO_DEBUG=False")
