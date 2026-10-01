from django.test import TestCase

from src.entities.branch.models import Branch
from src.entities.user.models import User
from src.services.token.jwt_implementation import JwtTokenService
from src.services.token.service import TokenType


class CreateBranchCompatibilityTests(TestCase):
    def setUp(self):
        user = User.objects.create(
            name="Admin", email="admin@example.test", password="unused",
            role="ADMIN", is_active=True,
        )
        token = JwtTokenService().sign(
            TokenType.AccessToken, {"sub": user.id, "role": "ADMIN"}
        ).token
        self.headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def post(self, body):
        return self.client.post("/create-branch", body, content_type="application/json", **self.headers)

    def test_requires_reference_dto_fields(self):
        response = self.post({"name": "Centro"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["name"], "InputValidationError")

    def test_validated_reference_payload_is_not_persisted(self):
        response = self.post({
            "id": 303, "name": "Centro", "city": "Fortaleza",
            "address": "Rua A", "ufId": 1,
        })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["name"], "PersistenceError")
        self.assertFalse(Branch.objects.filter(pk=303).exists())
