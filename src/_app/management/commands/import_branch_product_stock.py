"""Load the branch stock snapshot used by the planogram integration."""

import json
import math
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from src.entities.branch.models import Branch
from src.entities.product.models import BranchProductStock, Product


class Command(BaseCommand):
    help = "Imports a JSON stock snapshot using (sku, ean, branchId) as identity."

    def add_arguments(self, parser):
        parser.add_argument("file", help="JSON file containing a top-level array of stock rows")

    def handle(self, *args, **options):
        rows = self._read_rows(options["file"])
        normalized = [self._normalize(row, index) for index, row in enumerate(rows, start=1)]
        self._validate_identities(normalized)
        created = updated = 0
        with transaction.atomic():
            for row in normalized:
                if not Product.objects.filter(sku=row["sku"], ean=row["ean"]).exists():
                    raise CommandError(f"Linha {row['_line']}: produto ({row['sku']}, {row['ean']!r}) não encontrado.")
                if not Branch.objects.filter(pk=row["branch_id"]).exists():
                    raise CommandError(f"Linha {row['_line']}: filial {row['branch_id']} não encontrada.")
                _, was_created = BranchProductStock.objects.update_or_create(
                    sku=row["sku"], ean=row["ean"], branch_id=row["branch_id"],
                    defaults={"stock": row["stock"], "original_price": row["original_price"], "discount_price": row["discount_price"]},
                )
                created += was_created
                updated += not was_created
        self.stdout.write(self.style.SUCCESS(f"Estoque importado: {created} criado(s), {updated} atualizado(s)."))

    @staticmethod
    def _read_rows(filename):
        path = Path(filename)
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
        except OSError as error:
            raise CommandError(f"Não foi possível ler {path}: {error}") from error
        except json.JSONDecodeError as error:
            raise CommandError(f"JSON inválido em {path}: {error.msg}.") from error
        if not isinstance(content, list):
            raise CommandError("O JSON deve conter uma lista de linhas de estoque.")
        return content

    @staticmethod
    def _normalize(row, line):
        if not isinstance(row, dict):
            raise CommandError(f"Linha {line}: cada item deve ser um objeto JSON.")
        allowed = {"sku", "ean", "branchId", "stock", "originalPrice", "discountPrice"}
        missing = {"sku", "ean", "branchId", "stock"} - row.keys()
        extra = row.keys() - allowed
        if missing or extra:
            details = []
            if missing:
                details.append("ausentes: " + ", ".join(sorted(missing)))
            if extra:
                details.append("desconhecidos: " + ", ".join(sorted(extra)))
            raise CommandError(f"Linha {line}: campos inválidos ({'; '.join(details)}).")

        def integer(name):
            value = row[name]
            if isinstance(value, bool) or not isinstance(value, int):
                raise CommandError(f"Linha {line}: {name} deve ser inteiro.")
            return value

        def price(name):
            value = row.get(name)
            if value is None:
                return None
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise CommandError(f"Linha {line}: {name} deve ser número finito ou null.")
            return float(value)

        ean = row["ean"]
        if not isinstance(ean, str) or not ean:
            raise CommandError(f"Linha {line}: ean deve ser texto não vazio.")
        return {"_line": line, "sku": integer("sku"), "ean": ean, "branch_id": integer("branchId"),
                "stock": integer("stock"), "original_price": price("originalPrice"), "discount_price": price("discountPrice")}

    @staticmethod
    def _validate_identities(rows):
        seen = set()
        for row in rows:
            identity = (row["sku"], row["ean"], row["branch_id"])
            if identity in seen:
                raise CommandError(f"Linha {row['_line']}: identidade de estoque duplicada no arquivo.")
            seen.add(identity)
