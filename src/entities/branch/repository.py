import math

from django.core.exceptions import ValidationError
from django.db.models import F, Lookup, Q

from .models import Branch


class PrismaContains(Lookup):
    """Busca textual sem distinção de maiúsculas; % e _ permanecem curingas SQL."""
    lookup_name = "prisma_contains"

    def as_sql(self, compiler, connection):
        lhs, params = self.process_lhs(compiler, connection)
        _, rhs_params = self.process_rhs(compiler, connection)
        return f"{lhs} ILIKE %s", [*params, f"%{rhs_params[0]}%"]


class BranchRepository:
    """
    Encapsula o acesso a dados da entidade Branch.
    Centraliza as consultas e escritas de filiais.
    """

    def create(self, name: str, city: str, uf: str, address: str) -> Branch:
        return Branch.objects.create(name=name, city=city, uf=uf, address=address)

    def create_from_contract(self, data: dict) -> Branch:
        return Branch.objects.create(**data)

    def find_by_id(self, id: str) -> Branch | None:
        return Branch.objects.filter(id=id).first()

    def list_all(self):
        return Branch.objects.all()

    def filtered(self, filters, role, allowed_ids):
        from src.core.compatibility import js_number

        queryset = Branch.objects.all()
        if role not in ("ADMIN", "LAYOUT", "BACKOFFICE"):
            queryset = queryset.filter(id__in=allowed_ids or [])
        if filters.get("ufs"):
            queryset = queryset.filter(uf__in=filters["ufs"])
        search = filters.get("queryString")
        if search:
            condition = Q(PrismaContains(F("name"), search)) | Q(PrismaContains(F("city"), search))
            condition |= Q(PrismaContains(F("address"), search))
            number = js_number(search)
            if math.isfinite(number) and number == int(number):
                condition |= Q(id=int(number))
            queryset = queryset.filter(condition)
        return queryset

    def get(self, query, page_size, page_number):
        # A paginação usa apenas a parte inteira; deslocamentos negativos são inválidos.
        skip = (page_number - 1) * page_size if page_size and page_number else 0
        if not math.isfinite(page_size) or not math.isfinite(skip) or skip < 0:
            raise ValueError("Invalid Prisma pagination")
        take, skip = math.trunc(page_size), math.trunc(skip)
        # Layout is not modeled yet: every persisted branch really has no layout.
        rows = list(query.order_by("-id" if take < 0 else "id")[skip:skip + abs(take)])
        return list(reversed(rows)) if take < 0 else rows

    def count_branches(self, query):
        return query.count()

    def update(self, id: str, **fields) -> Branch | None:
        branch = self.find_by_id(id)
        if not branch:
            return None
        if set(fields) - {"name", "city", "address", "uf"}:
            raise ValidationError("Invalid Prisma branch update argument")
        for key, value in fields.items():
            if not isinstance(value, str):
                raise ValidationError("Invalid Prisma branch update value")
            setattr(branch, key, value)
        if fields:
            branch.save(update_fields=[*fields, "updated_at"])
        return branch

    def delete(self, id: str) -> bool:
        deleted, _ = Branch.objects.filter(id=id).delete()
        return deleted > 0
