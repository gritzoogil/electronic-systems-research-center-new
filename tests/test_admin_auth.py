import os
import unittest
from unittest.mock import patch

from app import create_app
import app.auth as auth_module


class AdminAuthTests(unittest.TestCase):
    def setUp(self):
        self.original_admin_emails = os.environ.get("ADMIN_EMAILS")
        os.environ["ADMIN_EMAILS"] = "admin@example.com"
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

    def tearDown(self):
        if self.original_admin_emails is None:
            os.environ.pop("ADMIN_EMAILS", None)
        else:
            os.environ["ADMIN_EMAILS"] = self.original_admin_emails

    def test_non_admin_user_receives_403(self):
        with patch.object(auth_module, "verify_id_token", return_value={"uid": "123", "email": "user@example.com"}):
            response = self.client.get(
                "/admin/me",
                headers={"Authorization": "Bearer test-token"},
            )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "admin_access_denied")

    def test_admin_user_is_allowed(self):
        with patch.object(auth_module, "verify_id_token", return_value={"uid": "123", "email": "admin@example.com"}):
            response = self.client.get(
                "/admin/me",
                headers={"Authorization": "Bearer test-token"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["email"], "admin@example.com")


if __name__ == "__main__":
    unittest.main()
