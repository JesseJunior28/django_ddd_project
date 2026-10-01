from django.test import TestCase

from src.entities.industry.models import Industry
from src.entities.user.models import User
from src.services.token.jwt_implementation import JwtTokenService
from src.services.token.service import TokenType


class IndustryEndpointsTests(TestCase):
    def setUp(self):
        user = User.objects.create(name="Admin", email="admin@example.test", password="x", role="ADMIN", is_active=True)
        token = JwtTokenService().sign(TokenType.AccessToken, {"sub": user.id, "role": "ADMIN"}).token
        self.headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_create_update_list_and_delete_protection(self):
        created = self.client.post("/create-industry", {"name": "Acme", "brands": ["One"]}, content_type="application/json", **self.headers)
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["brands"][0]["name"], "One")
        self.assertEqual(self.client.delete("/delete-industry/1", **self.headers).status_code, 500)
        updated = self.client.put("/update-industry", {"id": 1, "name": "Acme", "brandsToAdd": ["Two"]}, content_type="application/json", **self.headers)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual([item["name"] for item in updated.json()["brands"]], ["One", "Two"])
        self.assertEqual(Industry.objects.count(), 1)
