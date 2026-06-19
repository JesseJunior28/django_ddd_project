class ApplicationError(Exception):
    """Erros de infraestrutura/aplicação (ex: falha no banco, serviço externo)."""

    def __init__(self, message: str = "Application error"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class BusinessError(Exception):
    """Erros de regra de negócio (ex: entidade não encontrada, conflito)."""

    def __init__(self, message: str = "Business error"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class InputValidationError(ApplicationError):
    """Erro de validação de input. Equivalente ao InputValidationError do TS."""

    def __init__(self, message: str = "Input validation error"):
        super().__init__(message)


class UnknownError(ApplicationError):
    """Erro desconhecido/inesperado."""

    def __init__(self, message: str = "Unknown error"):
        super().__init__(message)


class NotFoundError(BusinessError):
    """Entidade não encontrada."""

    def __init__(self, entity: str = "Resource"):
        super().__init__(f"{entity} not found")


class ConflictError(BusinessError):
    """Conflito de dados (ex: registro já existe)."""

    def __init__(self, message: str = "Conflict"):
        super().__init__(message)
