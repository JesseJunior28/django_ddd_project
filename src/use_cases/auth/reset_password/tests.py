from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from src.entities.user.models import ResetToken, User
from src.services.hash.bcrypt_hasher import BcryptHashService
from src.services.token.jwt_implementation import JwtTokenService
from src.services.token.service import TokenType


class ResetPasswordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(name="Reset", email="reset@example.test", password="old-password",
                                        role="ADMIN", is_active=True)

    def send(self, data):
        return self.client.post("/send-reset-password-token", data, content_type="application/json")

    def reset(self, data):
        return self.client.post("/reset-password", data, content_type="application/json")

    def issue(self):
        with patch("src.services.email.smtp_implementation.SmtpEmailService.send_reset_password") as sender:
            response = self.send({"email": self.user.email})
        self.assertEqual(response.status_code, 200)
        sender.assert_called_once()
        return ResetToken.objects.get()

    def test_issue_emits_id_token_and_delivers_email(self):
        token = self.issue()
        claims = JwtTokenService().verify(token.token)
        self.assertFalse(claims.is_wrong())
        self.assertEqual(claims.value["sub"], self.user.id)
        self.assertEqual(claims.value["email"], self.user.email)
        self.assertEqual(claims.value["role"], "ADMIN")
        self.assertGreater(token.expires_at, timezone.now())

    def test_missing_inactive_and_roleless_users_do_not_create_tokens(self):
        for user, status, error in [
            (None, 404, "UserNotFound"),
            (User.objects.create(name="Inactive", email="inactive@example.test", password="x", role="ADMIN", is_active=False), 401, "UserBlocked"),
            (User.objects.create(name="Roleless", email="roleless@example.test", password="x", is_active=True), 401, "UserBlocked"),
        ]:
            with self.subTest(user=user):
                response = self.send({"email": user.email if user else "missing@example.test"})
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.json()["name"], error)
        self.assertFalse(ResetToken.objects.exists())

    def test_reset_changes_hash_and_consumes_token(self):
        token = self.issue()
        response = self.reset({"token": token.token, "password": "Changed-password!"})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(BcryptHashService().verify("Changed-password!", self.user.password))
        token.refresh_from_db()
        self.assertIsNotNone(token.used_at)
        response = self.reset({"token": token.token, "password": "Another-password!"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["name"], "InvalidResetToken")

    def test_expired_and_signed_but_unstored_tokens_do_not_change_password(self):
        token = self.issue()
        token.expires_at = timezone.now() - timedelta(seconds=1)
        token.save(update_fields=["expires_at"])
        before = self.user.password
        response = self.reset({"token": token.token, "password": "Changed-password!"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["name"], "ResetTokenExpiredError")
        unstored = JwtTokenService().sign(TokenType.IdToken, {
            "sub": self.user.id, "email": self.user.email, "role": self.user.role,
        }).token
        response = self.reset({"token": unstored, "password": "Changed-password!"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["name"], "InvalidResetToken")
        self.user.refresh_from_db()
        self.assertEqual(self.user.password, before)

    def test_validation_precedes_token_verification(self):
        for body in ({}, {"token": 1, "password": False}, {"token": "", "password": ""},
                     {"token": "invalid", "password": "short"}):
            response = self.reset(body)
            self.assertEqual(response.status_code, 400)
        self.assertFalse(ResetToken.objects.exists())
