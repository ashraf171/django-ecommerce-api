from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


User = get_user_model()


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            phone_number="123456789",
            address="Old Address",
        )

        self.client = APIClient()
        self.profile_url = "/api/v1/users/profile/"

    def test_unauthenticated_user_cannot_view_profile(self):
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_can_view_profile(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.user.id)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["phone_number"], self.user.phone_number)
        self.assertEqual(response.data["address"], self.user.address)

    def test_authenticated_user_can_update_profile_allowed_fields(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.put(
            self.profile_url,
            {
                "phone_number": "987654321",
                "address": "New Address",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()

        self.assertEqual(self.user.phone_number, "987654321")
        self.assertEqual(self.user.address, "New Address")