from django.test import TestCase

from src.entities.branch.models import Branch
from src.entities.user.models import User
from src.services.token.jwt_implementation import JwtTokenService
from src.services.token.service import TokenType


class BranchWriteTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            id=101,
            name="Centro",
            city="Fortaleza",
            uf="CE",
            address="Rua A",
        )
        self.admin = User.objects.create(
            name="Admin",
            email="admin@example.test",
            password="unused",
            role="ADMIN",
            is_active=True,
        )
        self.branch_user = User.objects.create(
            name="Branch",
            email="branch@example.test",
            password="unused",
            role="BRANCH",
            is_active=True,
        )
        tokens = JwtTokenService()
        self.admin_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {tokens.sign(TokenType.AccessToken, {'sub': self.admin.id, 'role': 'ADMIN'}).token}"
        }
        self.branch_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {tokens.sign(TokenType.AccessToken, {'sub': self.branch_user.id, 'role': 'BRANCH'}).token}"
        }

    def test_partial_update_preserves_unsupplied_values(self):
        response = self.client.put(
            "/update-branch",
            '{"id": 101, "name": "Novo Centro", "uf": "PI"}',
            content_type="application/json",
            **self.admin_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Novo Centro")
        self.assertEqual(response.json()["uf"], "PI")
        self.branch.refresh_from_db()
        self.assertEqual((self.branch.city, self.branch.address), ("Fortaleza", "Rua A"))

    def test_invalid_prisma_field_returns_stable_error_without_writing(self):
        response = self.client.put(
            "/update-branch",
            '{"id": 101, "ufId": 1}',
            content_type="application/json",
            **self.admin_headers,
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["name"], "PersistenceError")
        self.branch.refresh_from_db()
        self.assertEqual(self.branch.uf, "CE")

    def test_update_and_delete_require_admin(self):
        update = self.client.put(
            "/update-branch", '{"id": 101, "name": "Ignored"}',
            content_type="application/json", **self.branch_headers,
        )
        delete = self.client.delete("/delete-branch/101", **self.branch_headers)

        self.assertEqual(update.status_code, 403)
        self.assertEqual(delete.status_code, 403)

    def test_delete_returns_empty_success_then_not_found(self):
        response = self.client.delete("/delete-branch/101", **self.admin_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

        response = self.client.delete("/delete-branch/101", **self.admin_headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["name"], "BranchNotFoundError")
