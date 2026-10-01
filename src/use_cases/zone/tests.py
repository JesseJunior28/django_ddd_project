from django.test import TestCase

from src.entities.user.models import User
from src.services.token.jwt_implementation import JwtTokenService
from src.services.token.service import TokenType


class ZoneHierarchyTests(TestCase):
    def setUp(self):
        user = User.objects.create(name="Admin", email="admin@example.test", password="x", role="ADMIN", is_active=True)
        token = JwtTokenService().sign(TokenType.AccessToken, {"sub": user.id, "role": "ADMIN"}).token
        self.headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def request(self, path, data):
        return self.client.post(path, data, content_type="application/json", **self.headers)

    def test_hierarchy_blocks_parent_deletion_until_children_are_removed(self):
        self.assertEqual(self.request("/create-zone", {"name": "Zone", "hexColor": "#000"}).status_code, 201)
        self.assertEqual(self.request("/create-department", {"name": "Dept", "orientation": "ENTRY", "zoneId": 1}).status_code, 200)
        self.assertEqual(self.request("/create-level", {"name": "Level", "hexColor": "#fff", "divisions": ["A"], "departmentId": 1}).status_code, 201)
        self.assertEqual(self.client.delete("/delete-zone/1", **self.headers).status_code, 409)
        self.assertEqual(self.client.delete("/delete-department/1", **self.headers).status_code, 409)
        self.assertEqual(self.client.delete("/delete-level/1", **self.headers).status_code, 204)
        self.assertEqual(self.client.delete("/delete-department/1", **self.headers).status_code, 204)
        self.assertEqual(self.client.delete("/delete-zone/1", **self.headers).status_code, 204)
