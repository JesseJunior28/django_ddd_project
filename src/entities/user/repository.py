from datetime import datetime
from typing import Optional
import math

from django.db.models import QuerySet, F, Q
from django.core.exceptions import ValidationError
from src.entities.branch.repository import PrismaContains
from src.core.compatibility import js_number
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db import transaction

from .models import User, ResetToken


class UserRepository:
    """
    Só persiste. `password` já chega com hash — quem gera/verifica o hash
    é o use case, via HashService (src/services/hash).
    """

    @staticmethod
    def create(user_data: dict) -> User:
        return User.objects.create(**user_data)

    @staticmethod
    def create_registration(data):
        names = {"id": "id", "name": "name", "email": "email", "password": "password",
                 "role": "role", "isActive": "is_active", "itecUser": "itec_user",
                 "createdAt": "created_at", "updatedAt": "updated_at"}
        if set(data) - names.keys() - {"branches"}:
            raise ValidationError("Unknown persistence argument")
        values = {names[key]: value for key, value in data.items() if key in names}
        for field in ("id", "itec_user"):
            if field in values:
                UserRepository.validate_integer(values[field])
                values[field] = math.trunc(values[field])
        if "is_active" in values and type(values["is_active"]) is not bool:
            raise ValidationError("Invalid persistence boolean")
        user = User(**values)
        if "role" in values:
            User._meta.get_field("role").validate(user.role, user)
            if user.role == "":
                raise ValidationError("Invalid persistence enum")
        dates = {}
        for field in ("created_at", "updated_at"):
            if field in values:
                value = values[field]
                try:
                    parsed = parse_datetime(value) if isinstance(value, str) else None
                except ValueError:
                    parsed = None
                if parsed is None:
                    raise ValidationError("Invalid persistence date")
                dates[field] = timezone.make_aware(parsed, timezone.get_default_timezone()) if timezone.is_naive(parsed) else parsed
        # Dados do usuário e vínculos com filiais precisam ser gravados atomicamente.
        with transaction.atomic():
            user.save(force_insert=True)
            if dates:
                User.objects.filter(pk=user.pk).update(**dates)
            if "branches" in data:
                relations = data["branches"]
                if not isinstance(relations, dict) or set(relations) - {"connect"}:
                    raise ValidationError("Invalid branch connection")
                connects = relations.get("connect", [])
                if isinstance(connects, dict):
                    connects = [connects]
                if not isinstance(connects, list):
                    raise ValidationError("Invalid branch connection")
                ids = []
                for item in connects:
                    if not isinstance(item, dict) or set(item) != {"id"}:
                        raise ValidationError("Invalid branch selector")
                    UserRepository.validate_integer(item["id"])
                    ids.append(math.trunc(item["id"]))
                from src.entities.branch.models import Branch
                branches = list(Branch.objects.filter(id__in=ids))
                if len(branches) != len(set(ids)):
                    raise ValidationError("Missing branch connection")
                user.branches.add(*branches)
            user.refresh_from_db()
        return user

    @staticmethod
    def set_password(user_id: int, password_hash: str) -> Optional[User]:
        user = User.objects.filter(id=user_id).first()
        if not user:
            return None
        user.password = password_hash
        user.save(update_fields=["password", "updated_at"])
        return user

    @staticmethod
    def count_users(query: Optional[dict] = None) -> int:
        if isinstance(query, QuerySet):
            return query.count()
        queryset = User.objects.all()
        if query:
            queryset = queryset.filter(**query)
        return queryset.count()

    @staticmethod
    def filtered(filters):
        query = User.objects.all()
        if filters.get("isActive") is not None:
            query = query.filter(is_active=filters["isActive"])
        if filters.get("roles"):
            query = query.filter(role__in=filters["roles"])
        search = filters.get("queryString")
        if search:
            condition = Q(PrismaContains(F("name"), search)) | Q(PrismaContains(F("email"), search))
            number = js_number(search)
            if math.isfinite(number) and number == int(number):
                condition |= Q(itec_user=int(number))
            query = query.filter(condition)
        return query

    @staticmethod
    def page(query, page_size, page_number):
        skip = (page_number - 1) * page_size if page_size and page_number else 0
        if not math.isfinite(page_size) or not math.isfinite(skip) or skip < 0:
            raise ValueError("Invalid Prisma pagination")
        take, skip = math.trunc(page_size), math.trunc(skip)
        rows = list(query.order_by("-name" if take < 0 else "name")[skip:skip + abs(take)])
        return list(reversed(rows)) if take < 0 else rows

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
    def validate_integer(value):
        # Aceita apenas inteiros assinados de 32 bits; frações finitas são truncadas.
        if type(value) not in (int, float) or not math.isfinite(value) or not -(2**31) <= value < 2**31:
            raise ValidationError("Invalid persistence integer")

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
        UserRepository.validate_integer(itec_user)
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
            "password",
        ]
        for field in fields:
            if field in user_data:
                setattr(user, field, user_data[field])
        if "role" in user_data:
            # Validate choices at the persistence boundary, after service lookups.
            User._meta.get_field("role").validate(user.role, user)
            if user.role == "":
                raise ValidationError("Invalid persistence enum")
        if "itec_user" in user_data and user.itec_user is not None:
            UserRepository.validate_integer(user.itec_user)
            user.itec_user = math.trunc(user.itec_user)
        if "password" in user_data:
            value = user.password
            if isinstance(value, dict) and set(value) == {"set"}:
                value = value["set"]
            if not isinstance(value, str):
                raise ValidationError("Invalid persistence string")
            user.password = value
        # Uma atualização sem campos não deve alterar a data de modificação.
        changed = [field for field in fields if field in user_data]
        if changed:
            user.save(update_fields=changed + ["updated_at"])
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
