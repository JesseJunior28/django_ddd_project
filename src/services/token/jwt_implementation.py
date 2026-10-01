import re
import uuid
import time
from typing import Union

import jwt
from django.conf import settings

from src.core.either import Either, right, wrong
from .errors import InvalidTokenError, TokenExpiredError
from .service import (
    TokenType,
    TokenWrapper,
    AccessTokenPayload,
    IdTokenPayload,
    RefreshTokenPayload,
)

TokenPayload = Union[AccessTokenPayload, IdTokenPayload, RefreshTokenPayload]

# Nome da configuração que define a expiração de cada tipo de token.
_EXPIRES_IN_SETTING: dict[TokenType, str] = {
    TokenType.AccessToken: "JWT_ACCESS_TOKEN_EXPIRES_IN",
    TokenType.IdToken: "JWT_ID_TOKEN_EXPIRES_IN",
    TokenType.RefreshToken: "JWT_REFRESH_TOKEN_EXPIRES_IN",
}

# Valor esperado no cabeçalho JWT para cada tipo de token.
_TYP: dict[TokenType, str] = {
    TokenType.AccessToken: "at+jwt",
    TokenType.IdToken: "id+jwt",
    TokenType.RefreshToken: "rt+jwt",
}

_EXPIRES_IN_PATTERN = re.compile(r"^\s*(\d+)\s*([smhd])\s*$")
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def _parse_expires_in(expires_in: str) -> int:
    """
    Converte string de expiração (ex: '1h', '7d', '15m', '30s') para segundos.
    A unidade é obrigatória: uma duração sem unidade é ambígua demais para
    ser aceita em silêncio.
    """
    match = _EXPIRES_IN_PATTERN.match(expires_in)
    if not match:
        raise ValueError(
            f"Expiração JWT inválida: {expires_in!r}. Use <número><s|m|h|d>, ex: '15m', '7d'."
        )
    value, unit = match.groups()
    return int(value) * _UNIT_SECONDS[unit]


class JwtTokenService:
    """JWT emission/verification follow the distinct contracts in ADR-003."""

    def __init__(self):
        self.secret: str = settings.JWT_SECRET
        self.audience: str = settings.JWT_AUDIENCE
        self.issuer: str = settings.JWT_ISSUER
        # Parse na construção: configuração inválida falha logo, não no 1º login
        self._expires_in_seconds: dict[TokenType, int] = {
            token_type: _parse_expires_in(getattr(settings, setting_name))
            for token_type, setting_name in _EXPIRES_IN_SETTING.items()
        }

    def sign(
        self,
        token_type: TokenType,
        payload: dict,
    ) -> TokenWrapper:
        expires_in_seconds = self._expires_in_seconds[token_type]

        now = int(time.time())
        exp = now + expires_in_seconds

        claims = {
            **payload,
            # O identificador do sujeito é serializado como número no token.
            "sub": payload["sub"],
            "exp": exp,
            "iat": now,
            "aud": self.audience,
            "iss": self.issuer,
            "jti": str(uuid.uuid4()),
        }

        token = jwt.encode(
            claims,
            self.secret,
            algorithm="HS512",
            headers={"typ": _TYP[token_type]},
        )

        # expiresAt é expresso em milissegundos desde a época Unix.
        expires_at_ms = int(time.time() * 1000) + expires_in_seconds * 1000

        return TokenWrapper(token=token, expires_at=expires_at_ms)

    def verify(
        self,
        token: str,
        token_type: TokenType | None = None,
    ) -> Either[InvalidTokenError | TokenExpiredError, dict]:
        # A validação precisa conferir typ e tipos de claims em tempo de execução.
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=["HS256", "HS384", "HS512"],
                options={"verify_sub": False, "verify_jti": False, "verify_iat": False},
                audience=self.audience,
                issuer=self.issuer,
            )
        except jwt.ExpiredSignatureError:
            return wrong(TokenExpiredError())
        except jwt.InvalidTokenError:
            return wrong(InvalidTokenError())

        return right(payload)
