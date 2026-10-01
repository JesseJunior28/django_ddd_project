from typing import Protocol


class HashService(Protocol):
    """
    Contrato de hashing de senha.
    Implementação padrão: BcryptHashService com hashes no formato $2b$.
    """

    def hash(self, password: str) -> str: ...

    def verify(self, raw_password: str, hashed_password: str) -> bool: ...
