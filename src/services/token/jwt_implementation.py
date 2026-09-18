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

# Equivalente ao Record<TokenType, string> do TS — nome da setting de expiração
_EXPIRES_IN_SETTING: dict[TokenType, str] = {
    TokenType.AccessToken: "JWT_ACCESS_TOKEN_EXPIRES_IN",
    TokenType.IdToken: "JWT_ID_TOKEN_EXPIRES_IN",
    TokenType.RefreshToken: "JWT_REFRESH_TOKEN_EXPIRES_IN",
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


_EXPIRES_IN_PATTERN = re.compile(r"^\s*(\d+)\s*([smhd])\s*$")
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def _parse_expires_in(expires_in: str) -> int:
    """
    Converte string de expiração (ex: '1h', '7d', '15m', '30s') para segundos.
    A unidade é obrigatória: no ms() do Node, '3600' sem unidade seria
    3600 *milissegundos* — ambíguo demais para aceitar em silêncio.
    """
    match = _EXPIRES_IN_PATTERN.match(expires_in)
    if not match:
        raise ValueError(
            f"Expiração JWT inválida: {expires_in!r}. Use <número><s|m|h|d>, ex: '15m', '7d'."
        )
    value, unit = match.groups()
    return int(value) * _UNIT_SECONDS[unit]


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
            # RFC 7519 exige sub string — PyJWT >= 2.10 rejeita sub inteiro no decode
            "sub": str(payload["sub"]),
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
    ) -> Either[InvalidTokenError | TokenExpiredError, TokenPayload]:
        """
        Equivalente ao verify() do TS, mas no padrão Either do projeto:
        retorna wrong(TokenExpiredError | InvalidTokenError) ou right(payload).

        Rejeita token de outro tipo (ex: IdToken usado como AccessToken)
        comparando o header `typ` com o tipo esperado.
        """
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=["HS256"],
                audience=_AUDIENCE,
                issuer=_ISSUER,
            )
        except jwt.ExpiredSignatureError:
            return wrong(TokenExpiredError())
        except jwt.InvalidTokenError:
            return wrong(InvalidTokenError())

        # Seguro ler o header depois do decode: a assinatura já cobriu ele
        if jwt.get_unverified_header(token).get("typ") != _TYP[token_type]:
            return wrong(InvalidTokenError())

        try:
            return right(self._build_payload(token_type, payload))
        # KeyError/ValueError: claim obrigatória ausente ou sub não numérico
        except (KeyError, ValueError):
            return wrong(InvalidTokenError())

    @staticmethod
    def _build_payload(token_type: TokenType, payload: dict) -> TokenPayload:
        sub = int(payload["sub"])

        if token_type == TokenType.AccessToken:
            return AccessTokenPayload(
                sub=sub,
                role=payload["role"],
                allowed_branches_ids=payload.get("allowedBranchesIds"),
                exp=payload.get("exp"),
                iat=payload.get("iat"),
                aud=payload.get("aud"),
                iss=payload.get("iss"),
                jti=payload.get("jti"),
            )
        if token_type == TokenType.IdToken:
            return IdTokenPayload(
                sub=sub,
                email=payload["email"],
                role=payload["role"],
                exp=payload.get("exp"),
                iat=payload.get("iat"),
            )
        return RefreshTokenPayload(
            sub=sub,
            exp=payload.get("exp"),
            iat=payload.get("iat"),
        )
