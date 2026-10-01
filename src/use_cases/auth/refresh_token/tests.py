from django.test import TestCase

from src.entities.branch.models import Branch
from src.entities.user.models import User
from src.services.token.jwt_implementation import JwtTokenService
from src.services.token.service import TokenType


class RefreshTokenStateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(name="Refresh test", email="refresh@example.test",
                                        password="unused", role="ADMIN", is_active=True)
        self.tokens = JwtTokenService()
        self.refresh = self.tokens.sign(TokenType.RefreshToken, {"sub": self.user.id}).token

    def renew(self):
        return self.client.post("/refresh-token", {"refreshToken": self.refresh},
                                content_type="application/json")

    def claims(self, response):
        self.assertEqual(response.status_code, 200)
        result = self.tokens.verify(response.json()["accessToken"])
        self.assertFalse(result.is_wrong())
        return result.value

    def test_renewal_reads_changed_identity_and_branch_memberships(self):
        branch = Branch.objects.create(id=101, name="Branch", city="Fortaleza", uf="CE", address="Test")
        self.user.role = "BRANCH"
        self.user.email = "changed@example.test"
        self.user.save()
        self.user.branches.add(branch)
        claims = self.claims(self.renew())
        self.assertEqual(claims["role"], "BRANCH")
        self.assertEqual(claims["email"], "changed@example.test")
        self.assertEqual(claims["allowedBranchesIds"], [101])
        self.user.branches.clear()
        self.user.role = None
        self.user.save()
        claims = self.claims(self.renew())
        self.assertNotIn("allowedBranchesIds", claims)
        self.assertNotIn("role", claims)

    def test_disabling_then_deleting_user_invalidates_renewal(self):
        self.user.is_active = False
        self.user.save()
        response = self.renew()
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["name"], "UserBlocked")
        self.user.delete()
        response = self.renew()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["name"], "UserNotFound")

    def test_repeated_refresh_issues_unique_tokens_without_writing_user(self):
        original = User.objects.values().get(pk=self.user.id)
        identifiers = set()
        for _ in range(7):
            claims = self.claims(self.renew())
            self.assertNotIn(claims["jti"], identifiers)
            identifiers.add(claims["jti"])
        self.assertEqual(User.objects.values().get(pk=self.user.id), original)
