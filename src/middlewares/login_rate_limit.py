"""Reference login MemoryStore semantics: per process/IP, ten-minute window."""
import ipaddress
import math
import threading
import time

from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


class LoginRateLimitMiddleware(MiddlewareMixin):
    route_name = "login"
    request_attribute = "login_rate_limit"
    skip_successful = True
    error_name = "MaxUserLoginExceededError"
    error_message = "Usuário bloqueado por muitas tentativas falhas de login."

    @property
    def limit(self):
        return settings.MAX_LOGIN_TRIES

    def __init__(self, get_response):
        super().__init__(get_response)
        self.clients = {}
        self.lock = threading.Lock()
        self.next_cleanup = 0

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.resolver_match.url_name != self.route_name or request.method != "POST":
            return None
        # O último endereço encaminhado identifica o cliente atrás de um proxy confiável.
        key = request.headers.get("X-Forwarded-For", request.META.get("REMOTE_ADDR", ""))
        key = key.split(",")[-1].strip()
        try:
            address = ipaddress.ip_address(key)
            if address.version == 6:
                key = str(address.ipv4_mapped) if address.ipv4_mapped else str(
                    ipaddress.ip_network(f"{address}/56", strict=False))
        except ValueError:
            pass
        now = time.time()
        with self.lock:
            if now >= self.next_cleanup:
                self.clients = {k: v for k, v in self.clients.items() if v[1] > now}
                self.next_cleanup = now + 600
            hits, reset = self.clients.get(key, (0, now + 600))
            if reset <= now:
                hits, reset = 0, now + 600
            hits += 1
            self.clients[key] = (hits, reset)
        setattr(request, self.request_attribute, (key, hits, reset))
        if hits > self.limit:
            response = JsonResponse({"name": self.error_name, "message": self.error_message},
                                    status=429)
            response["Retry-After"] = str(max(0, math.ceil(reset - now)))
            return response

    def process_response(self, request, response):
        info = getattr(request, self.request_attribute, None)
        if info:
            key, hits, reset = info
            response["X-RateLimit-Limit"] = str(self.limit)
            response["X-RateLimit-Remaining"] = str(max(self.limit - hits, 0))
            response["X-RateLimit-Reset"] = str(math.ceil(reset))
            if self.skip_successful and response.status_code < 400:
                with self.lock:
                    current, current_reset = self.clients.get(key, (0, reset))
                    self.clients[key] = (max(0, current - 1), current_reset)
        return response
