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


  
if __name__ == "__main__":
    unittest.main()
