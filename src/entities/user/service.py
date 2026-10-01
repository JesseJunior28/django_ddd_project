import logging
from datetime import datetime, timezone as datetime_timezone

from django.utils import timezone

from src.core.either import right, wrong
from src.services.hash.bcrypt_hasher import BcryptHashService
from src.services.token.jwt_implementation import JwtTokenService
from src.services.token.service import TokenType
from .errors import (InvalidResetToken, ItecUserConflictError, ResetTokenExpiredError,
                     UserBlocked, UserNotFound, UserUnauthorizedError)
from .repository import UserRepository
from .errors import UserEmailAlreadyExists, UserItecAlreadyExists

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, repository=None, hash_service=None, token_service=None):
        self.repository = repository or UserRepository()
        self.hash_service = hash_service or BcryptHashService()
        self.token_service = token_service or JwtTokenService()

    def create_user(self, data):
        if self.repository.get({"email": data["email"]}).exists():
            return wrong(UserEmailAlreadyExists())
        if data.get("itecUser"):
            if self.repository.get_by_itec_user(data["itecUser"]):
                return wrong(UserItecAlreadyExists())
        password_hash = self.hash_service.hash(data["password"])
        user = self.repository.create_registration({**data, "password": password_hash})
        return right(self.map_to_entity(user))

    def get_user(self, user_id):
        user = self.repository.get_by_id(user_id)
        return right(user) if user else wrong(UserNotFound())

    @staticmethod
    def map_to_entity(user):
        def date(value):
            return value.astimezone(datetime_timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        return {"id": user.id, "email": user.email, "name": user.name,
                **({"role": user.role} if user.role else {}),
                "isActive": user.is_active,
                **({"itecUser": user.itec_user} if user.itec_user else {}),
                "createdAt": date(user.created_at), "updatedAt": date(user.updated_at)}

    def get_users(self, query, page_size, page_number):
        try:
            return [self.map_to_entity(user) for user in self.repository.page(query, page_size, page_number)]
        except Exception:
            logger.warning("UserService.get_users failed")
            return []

    def update_user(self, data):
        self.repository.validate_integer(data["id"])
        user = self.repository.get_by_id(data["id"])
        if not user:
            return wrong(UserNotFound())
        if data.get("itecUser"):
            existing = self.repository.get_by_itec_user(data["itecUser"])
            if existing and existing.id != user.id:
                return wrong(ItecUserConflictError(data["itecUser"]))
        names = {"id": "id", "name": "name", "itecUser": "itec_user", "role": "role",
                 "isActive": "is_active", "password": "password"}
        updated = self.repository.update({names[key]: value for key, value in data.items() if key in names})
        return right(self.map_to_entity(updated))

    def get_user_branches_ids(self, user_id):
        try:
            user = self.repository.get_by_id(user_id)
            return [branch.id for branch in user.branches.all()] if user else []
        except Exception:
            logger.warning("UserService.get_user_branches_ids failed")
            return []

    def validate_credentials(self, credentials):
        user = self.repository.get_by_email(credentials["email"])
        if user is None:
            return wrong(UserNotFound())
        if not self.hash_service.verify(credentials["password"], user.password):
            return wrong(UserUnauthorizedError())
        if not user.is_active or not user.role:
            return wrong(UserBlocked())
        claims = {"sub": user.id, "email": user.email, "role": user.role}
        branches = [branch.id for branch in user.branches.all()]
        if branches:
            claims["allowedBranchesIds"] = branches
        access = self.token_service.sign(TokenType.AccessToken, claims)
        refresh = self.token_service.sign(TokenType.RefreshToken, {"sub": user.id})
        return right({"accessToken": access.token, "refreshToken": refresh.token,
                      "expiresAt": access.expires_at})

    def get_reset_password_data(self, email):
        user = self.repository.get_by_email(email)
        if not user:
            return wrong(UserNotFound())
        if not user.is_active or not user.role:
            return wrong(UserBlocked())
        token = self.token_service.sign(TokenType.IdToken, {
            "sub": user.id, "email": user.email, "role": user.role,
        })
        self.repository.create_reset_token({
            "user_id": user.id,
            "token": token.token,
            "expires_at": datetime.fromtimestamp(token.expires_at / 1000, tz=datetime_timezone.utc),
        })
        return right({"userName": user.name, "userEmail": user.email, "token": token.token})

    def verify_reset_token(self, user_id, token):
        token_data = self.repository.get_reset_token(token)
        if not token_data or token_data.user_id != user_id or token_data.used_at:
            return wrong(InvalidResetToken())
        if token_data.expires_at < timezone.now():
            return wrong(ResetTokenExpiredError())
        return right(token_data.id)

    def reset_password(self, user_id, password, token_id):
        user = self.repository.get_by_id(user_id)
        if not user:
            return wrong(UserNotFound())
        self.repository.set_password(user_id, self.hash_service.hash(password))
        self.repository.update_reset_token_used_at(token_id, timezone.now())
        return right(None)
