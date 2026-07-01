from datetime import datetime
from typing import Any, Optional

from django.contrib.auth.hashers import make_password, check_password
from django.db.models import QuerySet
from django.utils import timezone

from .models import User, ResetToken


class UserRepository:
    @staticmethod
    def create(user_data: dict) -> User:
        
        user_data = dict[Any, Any](user_data) 
        if "password" in user_data:
            user_data["password"] = make_password(user_data["password"])
        return User.objects.create(**user_data)

    @staticmethod
    def check_password(user: User, raw_password: str) -> bool:
        return check_password(raw_password, user.password)

    @staticmethod
    def set_password(user_id: int, raw_password: str) -> Optional[User]:
        
        user = User.objects.filter(id=user_id).first()
        if not user:
            return None
        user.password = make_password(raw_password)
        user.save(update_fields=["password", "updated_at"])
        return user

    @staticmethod
    def count_users(query: Optional[dict] = None) -> int:
        queryset = User.objects.all()
        if query:
            queryset = queryset.filter(**query)
        return queryset.count()

    @staticmethod
    def get(
        query: Optional[dict] = None,
        page_size: Optional[int] = None,
        page_number: Optional[int] = None,
    ) -> QuerySet[User]:
        queryset = User.objects.filter(**query) if query else User.objects.all()
        queryset = queryset.order_by("name") 
        if page_size and page_number:
            start = (page_number - 1) * page_size
            end = start + page_size
            queryset = queryset[start:end]
        return queryset

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        return (
            User.objects
            .prefetch_related("branches")
            .filter(id=user_id)
            .first()
        )

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        return (
            User.objects
            .prefetch_related("branches")
            .filter(email=email)
            .first()
        )

    @staticmethod
    def get_by_itec_user(itec_user: int) -> Optional[User]:
        return User.objects.filter(itec_user=itec_user).first()

    @staticmethod
    def get_by_branch_id(
        branch_id: int,
        roles: Optional[list] = None,
    ) -> QuerySet[User]:
        queryset = User.objects.filter(
            branches__id=branch_id
        )
        if roles:
            queryset = queryset.filter(role__in=roles)
        return queryset.distinct()

    @staticmethod
    def update(user_data: dict) -> Optional[User]:
        user = User.objects.filter(id=user_data["id"]).first()
        if not user:
            return None
        fields = [
            "name",
            "itec_user",
            "is_active",
            "role",
        ]
        for field in fields:
            if field in user_data:
                setattr(user, field, user_data[field])
        user.save()
        return user

    @staticmethod
    def create_reset_token(token_data: dict) -> ResetToken:
        return ResetToken.objects.create(**token_data)

    @staticmethod
    def get_reset_token(token: str) -> Optional[ResetToken]:
        return ResetToken.objects.filter(token=token).first()

    @staticmethod
    def get_valid_reset_token(token: str) -> Optional[ResetToken]:
        return ResetToken.objects.filter(
            token=token,
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).first()

    @staticmethod
    def update_reset_token_used_at(
        token_id: int,
        used_at: datetime,
    ) -> Optional[ResetToken]:
        reset_token = ResetToken.objects.filter(id=token_id).first()
        if not reset_token:
            return None
        reset_token.used_at = used_at
        reset_token.save()
        return reset_token