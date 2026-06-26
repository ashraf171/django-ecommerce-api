from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from django.core.cache import cache
from rest_framework.throttling import ScopedRateThrottle
from rest_framework import status
from rest_framework.test import APITestCase

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
        









TEST_THROTTLE_RATES = {
    "login": "2/min",
    "checkout": "2/min",
    "product_list": "2/min",
}


class RateLimitingTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.original_throttle_rates = ScopedRateThrottle.THROTTLE_RATES.copy()
        ScopedRateThrottle.THROTTLE_RATES = TEST_THROTTLE_RATES

    def tearDown(self):
        ScopedRateThrottle.THROTTLE_RATES = self.original_throttle_rates
        cache.clear()

    def test_login_rate_limit_returns_429(self):
        User = get_user_model()

        User.objects.create_user(
            username="testuser",
            password="StrongPass123"
        )

        url = "/api/v1/auth/jwt/create/"

        payload = {
            "username": "testuser",
            "password": "WrongPassword"
        }

        response_1 = self.client.post(url, payload, format="json")
        response_2 = self.client.post(url, payload, format="json")
        response_3 = self.client.post(url, payload, format="json")

        self.assertNotEqual(response_1.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertNotEqual(response_2.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response_3.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_product_list_rate_limit_returns_429(self):
        url = "/api/v1/products/product/"

        response_1 = self.client.get(url)
        response_2 = self.client.get(url)
        response_3 = self.client.get(url)

        self.assertNotEqual(response_1.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertNotEqual(response_2.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response_3.status_code, status.HTTP_429_TOO_MANY_REQUESTS)