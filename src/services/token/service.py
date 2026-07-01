from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TokenType(str, Enum):
    AccessToken = "AccessToken"
    IdToken = "IdToken"
    RefreshToken = "RefreshToken"


@dataclass
class TokenWrapper:
    token: str
    expires_at: int  


@dataclass
class AccessTokenPayload:
    sub: int
    role: str
    allowed_branches_ids: Optional[list[int]] = None
    # campos padrão JWT (preenchidos pelo PyJWT no verify)
    exp: Optional[int] = None
    iat: Optional[int] = None
    aud: Optional[str] = None
    iss: Optional[str] = None
    jti: Optional[str] = None


@dataclass
class IdTokenPayload:
    sub: int
    email: str
    role: str
    exp: Optional[int] = None
    iat: Optional[int] = None


@dataclass
class RefreshTokenPayload:
    sub: int
    exp: Optional[int] = None
    iat: Optional[int] = None
