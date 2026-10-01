from django.test import TestCase
from src.entities.branch.models import Branch
from src.entities.user.models import User
from src.services.token.jwt_implementation import JwtTokenService
from src.services.token.service import TokenType


class UpdateUserStateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(name="Original", email="update@example.test",
                                        password="original hash", role="ADMIN", is_active=True)
        self.other = User.objects.create(name="Other", email="other@example.test", password="other", itec_user=123)
        self.branch = Branch.objects.create(id=101, name="Branch", city="Fortaleza", uf="CE", address="Test")
        self.user.branches.add(self.branch)
        self.token = JwtTokenService().sign(TokenType.AccessToken, {"sub": self.user.id, "role": "ADMIN"}).token

    def update(self, data):
        return self.client.put("/update-user", data, content_type="application/json",
                               HTTP_AUTHORIZATION="Bearer " + self.token)

    def state(self):
        return list(User.objects.order_by("id").values()), list(self.user.branches.values_list("id", flat=True))

    def test_partial_update_preserves_password_email_and_relations(self):
        response = self.update({"id": self.user.id, "name": "Changed", "role": "LAYOUT",
                                "isActive": False, "email": "ignored@test", "branches": []})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Changed")
        self.assertEqual(self.user.role, "LAYOUT")
        self.assertFalse(self.user.is_active)
        self.assertEqual(self.user.email, "update@example.test")
        self.assertEqual(self.user.password, "original hash")
        self.assertEqual(list(self.user.branches.values_list("id", flat=True)), [101])
        self.assertNotIn("password", response.json())

    def test_internal_failures_do_not_write_any_field(self):
        before = self.state()
        for fields in ({"role": "UNKNOWN"}, {"role": ""},
                       {"password": None}, {"password": 3}, {"id": 2147483648}):
            with self.subTest(fields=fields):
                response = self.update({"id": self.user.id, "name": "Must not persist", **fields})
                self.assertEqual(response.status_code, 500)
                self.assertEqual(response.json()["name"], "PersistenceError")
                self.assertEqual(self.state(), before)

    def test_conflict_and_lookup_precede_enum_validation(self):
        before = self.state()
        response = self.update({"id": self.user.id, "itecUser": 123, "role": "UNKNOWN"})
        self.assertEqual(response.status_code, 409)
        response = self.update({"id": 999999, "itecUser": 123, "role": "UNKNOWN"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.state(), before)

    def test_zero_unique_failure_rolls_back_and_is_not_business_conflict(self):
        self.other.itec_user = 0
        self.other.save()
        before = self.state()
        response = self.update({"id": self.user.id, "itecUser": 0, "name": "Must not persist"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["name"], "PersistenceError")
        self.assertEqual(self.state(), before)

    def test_empty_update_keeps_timestamp(self):
        before = self.state()
        self.assertEqual(self.update({"id": self.user.id}).status_code, 200)
        self.assertEqual(self.state(), before)

    def test_reference_password_passthrough_and_set_operation(self):
        for password in ("reference passthrough", {"set": "reference set"}):
            response = self.update({"id": self.user.id, "password": password})
            self.assertEqual(response.status_code, 200)
            self.user.refresh_from_db()
            self.assertEqual(self.user.password, password if isinstance(password, str) else password["set"])
            self.assertNotIn("password", response.json())

    def test_fractional_identifiers_follow_reference_truncation(self):
        response = self.update({"id": self.user.id + .5, "itecUser": 1.5})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.itec_user, 1)
