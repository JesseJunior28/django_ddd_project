import bcrypt as _bcrypt


class BcryptHashService:
    """
    Serviço de hashing de senha com bcrypt.

    Por que não usar o sistema de hashers do Django (make_password/check_password)?
    O Django identifica o hasher pelo prefixo do hash (ex: 'pbkdf2_sha256$...',
    'bcrypt$...'). Hashes gerados pelo bcrypt puro ($2b$...) não têm esse
    prefixo, então o Django não consegue identificar qual hasher usar.
    Em vez de forçar adaptações frágeis, usamos o bcrypt diretamente.

    Isso mantém os hashes verificáveis por qualquer processo que use bcrypt.
    """

    def hash(self, password: str) -> str:
        """Gera um hash bcrypt para a senha."""
        salt = _bcrypt.gensalt()
        return _bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify(self, raw_password: str, hashed_password: str) -> bool:
        """Compara uma senha com seu hash bcrypt."""
        try:
            return _bcrypt.checkpw(
                raw_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except Exception:
            return False
