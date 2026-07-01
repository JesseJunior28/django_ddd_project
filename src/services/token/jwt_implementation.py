import uuid
import time
from typing import Union

import jwt
from django.conf import settings

from .errors import InvalidTokenError, TokenExpiredError
from .service import (
    TokenType,
    TokenWrapper,
    AccessTokenPayload,
    IdTokenPayload,
    RefreshTokenPayload,
)


# Equivalente ao Record<TokenType, string> do TS
_EXPIRES_IN: dict[TokenType, str] = {
    TokenType.AccessToken: lambda: settings.JWT_ACCESS_TOKEN_EXPIRES_IN,
    TokenType.IdToken: lambda: settings.JWT_ID_TOKEN_EXPIRES_IN,
    TokenType.RefreshToken: lambda: settings.JWT_REFRESH_TOKEN_EXPIRES_IN,
}

# Equivalente ao typ Record<TokenType, string> do TS
_TYP: dict[TokenType, str] = {
    TokenType.AccessToken: "at+jwt",
    TokenType.IdToken: "id+jwt",
    TokenType.RefreshToken: "rt+jwt",
}

# Audience e issuer — idênticos ao JwtTokenService.ts
_AUDIENCE = "gestao-por-espaco"
_ISSUER = "https://ge.drogariaglobo.com.br"


def _parse_expires_in(expires_in: str) -> int:
    """
    Converte string de expiração (ex: '1h', '7d', '15m') para segundos.
    Equivalente ao ms() do Node.js.
    """
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    unit = expires_in[-1]
    value = int(expires_in[:-1])
    return value * units.get(unit, 1)


class JwtTokenService:
    """
    Equivalente ao JwtTokenService do backend TS.

    Configurações replicadas fielmente:
    - algorithm: HS256 (PyJWT usa isso para assinar)
    - header typ: at+jwt / id+jwt / rt+jwt por tipo de token
    - audience: gestao-por-espaco
    - issuer: https://ge.drogariaglobo.com.br
    - jwtid: UUID v4 gerado a cada sign()
    - expiresAt: timestamp em ms (igual ao TS)
    - secret: settings.JWT_SECRET (variável de ambiente JWT_SECRET)
    """

    def __init__(self):
        self.secret: str = settings.JWT_SECRET

    def sign(
        self,
        token_type: TokenType,
        payload: dict,
    ) -> TokenWrapper:
        expires_in_str = _EXPIRES_IN[token_type]()
        expires_in_seconds = _parse_expires_in(expires_in_str)

        now = int(time.time())
        exp = now + expires_in_seconds

        claims = {
            **payload,
            "exp": exp,
            "iat": now,
            "aud": _AUDIENCE,
            "iss": _ISSUER,
            "jti": str(uuid.uuid4()),
        }

        token = jwt.encode(
            claims,
            self.secret,
            algorithm="HS256",
            headers={"typ": _TYP[token_type]},
        )

        # expiresAt em ms, igual ao return do TS: add(new Date(), { seconds }).getTime()
        expires_at_ms = exp * 1000

        return TokenWrapper(token=token, expires_at=expires_at_ms)

    def verify(
        self,
        token: str,
        token_type: TokenType,
    ) -> Union[AccessTokenPayload, IdTokenPayload, RefreshTokenPayload]:
        """
        Equivalente ao verify() do TS. Mapeia os erros do PyJWT para
        InvalidTokenError / TokenExpiredError, exatamente como no TS.
        """
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=["HS256"],
                audience=_AUDIENCE,
                issuer=_ISSUER,
            )

            if token_type == TokenType.AccessToken:
                return AccessTokenPayload(
                    sub=payload["sub"],
                    role=payload["role"],
                    allowed_branches_ids=payload.get("allowedBranchesIds"),
                    exp=payload.get("exp"),
                    iat=payload.get("iat"),
                    aud=payload.get("aud"),
                    iss=payload.get("iss"),
                    jti=payload.get("jti"),
                )
            elif token_type == TokenType.IdToken:
                return IdTokenPayload(
                    sub=payload["sub"],
                    email=payload["email"],
                    role=payload["role"],
                    exp=payload.get("exp"),
                    iat=payload.get("iat"),
                )
            else:  # RefreshToken
                return RefreshTokenPayload(
                    sub=payload["sub"],
                    exp=payload.get("exp"),
                    iat=payload.get("iat"),
                )

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except (jwt.InvalidTokenError, jwt.DecodeError, jwt.InvalidSignatureError):
            raise InvalidTokenError()
