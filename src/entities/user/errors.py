from src.errors.domain_errors import BusinessError


class UserNotFound(BusinessError):
    def __init__(self):
        super().__init__("Usuário não encontrado.")


class UserUnauthorizedError(BusinessError):
    def __init__(self):
        super().__init__("Email ou senha inválidos.")


class UserBlocked(BusinessError):
    def __init__(self):
        super().__init__("Usuário bloqueado no sistema.")


class ItecUserConflictError(BusinessError):
    def __init__(self, code):
        super().__init__(f"Já existe um usuário com o código itec {code}.")


class UserEmailAlreadyExists(BusinessError):
    def __init__(self):
        super().__init__("Email já é utilizado por outro usuário.")


class UserItecAlreadyExists(BusinessError):
    def __init__(self):
        super().__init__("Código Itec já é utilizado por outro usuário.")


class InvalidResetToken(BusinessError):
    def __init__(self):
        super().__init__("O token para resetar a senha é inválido.")


class ResetTokenExpiredError(BusinessError):
    def __init__(self):
        super().__init__("O token para resetar a senha expirou.")
