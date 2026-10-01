from src.errors.domain_errors import BusinessError


class InvalidTokenError(BusinessError):
    def __init__(self):
        super().__init__("O token é inválido.")


class TokenExpiredError(BusinessError):
    def __init__(self):
        super().__init__("O token expirou.")
