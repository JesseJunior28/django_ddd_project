from typing import Protocol


class HashService(Protocol):
    """
    Contrato de hashing de senha — equivalente à interface HashService do TS.
    Implementação padrão: BcryptHashService (hashes $2b$, compatíveis com o TS).
    """

    def hash(self, password: str) -> str: ...

    def verify(self, raw_password: str, hashed_password: str) -> bool: ...
