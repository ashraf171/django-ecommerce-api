from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from product.models import Category, Product


User = get_user_model()


class ProductTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="normaluser",
            email="user@example.com",
            password="testpass123"
        )

        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123"
        )

        self.client = APIClient()

        self.products_url = reverse("product-list")

        self.electronics = Category.objects.create(
            name="Electronics",
            slug="electronics"
        )

        self.fashion = Category.objects.create(
            name="Fashion",
            slug="fashion"
        )

        self.iphone = Product.objects.create(
            category=self.electronics,
            name="iPhone 15",
            description="Apple smartphone",
            price=Decimal("1000.00"),
            in_stock=10
        )

        self.samsung = Product.objects.create(
            category=self.electronics,
            name="Samsung S24",
            description="Android smartphone",
            price=Decimal("800.00"),
            in_stock=15
        )

        self.tshirt = Product.objects.create(
            category=self.fashion,
            name="Black T-Shirt",
            description="Cotton shirt",
            price=Decimal("25.00"),
            in_stock=50
        )

    def get_results(self, response):
        data = response.data

        if isinstance(data, dict) and "results" in data:
            return data["results"]

        return data

    def test_search_products_by_name(self):
        response = self.client.get(self.products_url, {"search": "iphone"})

        self.assertEqual(response.status_code, 200)

        results = self.get_results(response)
        names = [item["name"] for item in results]

        self.assertIn("iPhone 15", names)

    def test_filter_products_by_min_price(self):
        response = self.client.get(self.products_url, {"min_price": 500})

        self.assertEqual(response.status_code, 200)

        results = self.get_results(response)
        names = [item["name"] for item in results]

        self.assertIn("iPhone 15", names)
        self.assertIn("Samsung S24", names)
        self.assertNotIn("Black T-Shirt", names)

    def test_filter_products_by_max_price(self):
        response = self.client.get(self.products_url, {"max_price": 100})

        self.assertEqual(response.status_code, 200)

        results = self.get_results(response)
        names = [item["name"] for item in results]

        self.assertIn("Black T-Shirt", names)
        self.assertNotIn("iPhone 15", names)

    def test_filter_products_by_category_slug(self):
        response = self.client.get(
            self.products_url,
            {"category": "electronics"}
        )

        self.assertEqual(response.status_code, 200)

        results = self.get_results(response)
        names = [item["name"] for item in results]

        self.assertIn("iPhone 15", names)
        self.assertIn("Samsung S24", names)
        self.assertNotIn("Black T-Shirt", names)

    def test_order_products_by_price_desc(self):
        response = self.client.get(
            self.products_url,
            {"ordering": "-price"}
        )

        self.assertEqual(response.status_code, 200)

        results = self.get_results(response)

        self.assertEqual(results[0]["name"], "iPhone 15")
        self.assertEqual(results[1]["name"], "Samsung S24")
        self.assertEqual(results[2]["name"], "Black T-Shirt")

    def test_normal_user_cannot_create_product(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.products_url,
            {
                "category": self.electronics.id,
                "name": "MacBook Pro",
                "description": "Apple laptop",
                "price": "2000.00",
                "in_stock": 5
            },
            format="json"
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_product(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            self.products_url,
            {
                "category": self.electronics.id,
                "name": "MacBook Pro",
                "description": "Apple laptop",
                "price": "2000.00",
                "in_stock": 5
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Product.objects.filter(name="MacBook Pro").exists())