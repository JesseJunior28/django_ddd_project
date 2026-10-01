from django.test import TestCase


class SendResetPasswordTokenValidationTests(TestCase):
    def test_email_validation(self):
        for body in ({}, {"email": None}, {"email": ""}, {"email": 1}, {"email": "invalid"}):
            response = self.client.post("/send-reset-password-token", body, content_type="application/json")
            self.assertEqual(response.status_code, 400)
