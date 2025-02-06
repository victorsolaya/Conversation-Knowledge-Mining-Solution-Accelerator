import unittest
from unittest.mock import patch
import base64
import json
from auth.auth_utils import get_authenticated_user_details, get_tenantid

class TestAuthUtils(unittest.TestCase):

    def test_get_authenticated_user_details_with_headers(self):
        request_headers = {
            "X-Ms-Client-Principal-Id": "user123",
            "X-Ms-Client-Principal-Name": "John Doe",
            "X-Ms-Client-Principal-Idp": "aad",
            "X-Ms-Token-Aad-Id-Token": "token123",
            "X-Ms-Client-Principal": "base64string"
        }

        user_details = get_authenticated_user_details(request_headers)

        self.assertEqual(user_details["user_principal_id"], "user123")
        self.assertEqual(user_details["user_name"], "John Doe")
        self.assertEqual(user_details["auth_provider"], "aad")
        self.assertEqual(user_details["auth_token"], "token123")
        self.assertEqual(user_details["client_principal_b64"], "base64string")

    @patch("App.backend.auth.auth_utils.sample_user.sample_user", {
        "X-Ms-Client-Principal-Id": "dev-user",
        "X-Ms-Client-Principal-Name": "Dev User",
        "X-Ms-Client-Principal-Idp": "dev-idp",
        "X-Ms-Token-Aad-Id-Token": "dev-token",
        "X-Ms-Client-Principal": "dev-base64"
    })
    def test_get_authenticated_user_details_without_headers(self, mock_sample_user):
        request_headers = {}

        user_details = get_authenticated_user_details(request_headers)

        self.assertEqual(user_details["user_principal_id"], "dev-user")
        self.assertEqual(user_details["user_name"], "Dev User")
        self.assertEqual(user_details["auth_provider"], "dev-idp")
        self.assertEqual(user_details["auth_token"], "dev-token")
        self.assertEqual(user_details["client_principal_b64"], "dev-base64")

    def test_get_tenantid_with_valid_base64(self):
        user_info = {"tid": "tenant123"}
        encoded_info = base64.b64encode(json.dumps(user_info).encode("utf-8"))

        tenant_id = get_tenantid(encoded_info.decode("utf-8"))

        self.assertEqual(tenant_id, "tenant123")

    def test_get_tenantid_with_invalid_base64(self):
        invalid_base64 = "invalid_base64"

        tenant_id = get_tenantid(invalid_base64)

        self.assertEqual(tenant_id, "")

    def test_get_tenantid_with_empty_base64(self):
        tenant_id = get_tenantid("")

        self.assertEqual(tenant_id, "")

if __name__ == "__main__":
    unittest.main()
