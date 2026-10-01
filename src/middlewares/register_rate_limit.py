from .login_rate_limit import LoginRateLimitMiddleware


class RegisterRateLimitMiddleware(LoginRateLimitMiddleware):
    route_name = "register"
    request_attribute = "register_rate_limit"
    skip_successful = False
    error_name = "UserMaxRegisterExceededError"
    error_message = "Usuário bloqueado por muitas tentativas de criação de usuário."
    limit = 3
