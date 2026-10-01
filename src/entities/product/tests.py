import json
from io import StringIO
from tempfile import NamedTemporaryFile

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError
from django.test import TestCase

from src.entities.branch.models import Branch
from src.entities.product.models import BranchProductStock, Product


class BranchProductStockTests(TestCase):
    def test_stock_identity_is_unique_per_branch(self):
        first = Branch.objects.create(id=1, name="Centro", city="Fortaleza", uf="CE", address="Rua 1")
        second = Branch.objects.create(id=2, name="Norte", city="Teresina", uf="PI", address="Rua 2")
        BranchProductStock.objects.create(branch=first, sku=10, ean="789", stock=4)
        BranchProductStock.objects.create(branch=second, sku=10, ean="789", stock=8)

        with self.assertRaises(IntegrityError):
            BranchProductStock.objects.create(branch=first, sku=10, ean="789", stock=2)


class ImportBranchProductStockCommandTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(id=11, name="Centro", city="Fortaleza", uf="CE", address="Rua 1")
        Product.objects.create(sku=10, ean="789", name="Produto", width=1, height=1)

    def run_import(self, rows):
        with NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as source:
            json.dump(rows, source)
            source.flush()
            output = StringIO()
            call_command("import_branch_product_stock", source.name, stdout=output)
            return output.getvalue()

    def test_import_is_idempotent_and_updates_by_composite_identity(self):
        row = {"sku": 10, "ean": "789", "branchId": 11, "stock": 4, "originalPrice": 12.5, "discountPrice": None}
        self.assertIn("1 criado(s), 0 atualizado(s)", self.run_import([row]))
        row["stock"] = 9
        row["discountPrice"] = 10
        self.assertIn("0 criado(s), 1 atualizado(s)", self.run_import([row]))
        stock = BranchProductStock.objects.get()
        self.assertEqual((stock.stock, stock.original_price, stock.discount_price), (9, 12.5, 10))

    def test_invalid_row_rolls_back_the_entire_snapshot(self):
        rows = [{"sku": 10, "ean": "789", "branchId": 11, "stock": 4}, {"sku": 99, "ean": "missing", "branchId": 11, "stock": 3}]
        with self.assertRaisesMessage(CommandError, "produto (99, 'missing') não encontrado"):
            self.run_import(rows)
        self.assertFalse(BranchProductStock.objects.exists())

    def test_duplicate_identity_is_rejected_before_writes(self):
        row = {"sku": 10, "ean": "789", "branchId": 11, "stock": 4}
        with self.assertRaisesMessage(CommandError, "identidade de estoque duplicada"):
            self.run_import([row, row])
        self.assertFalse(BranchProductStock.objects.exists())
