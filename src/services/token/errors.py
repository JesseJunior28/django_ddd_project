from src.errors.domain_errors import BusinessError


class InvalidTokenError(BusinessError):
    def __init__(self):
        super().__init__("Invalid token")


class TokenExpiredError(BusinessError):
    def __init__(self):
        super().__init__("Token expired")
