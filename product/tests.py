from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient,APITestCase
from django.core.cache import cache
from product.models import Category, Product


User = get_user_model()


class ProductTests(TestCase):
    def setUp(self):
        cache.clear()
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


    def test_product_list_cache_is_invalidated_when_admin_creates_product(self):
        first_response = self.client.get(self.products_url)
        self.assertEqual(first_response["X-Cache"], "MISS")

        second_response = self.client.get(self.products_url)
        self.assertEqual(second_response["X-Cache"], "HIT")

        self.client.force_authenticate(user=self.admin)

        create_response = self.client.post(
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

        self.assertEqual(create_response.status_code, 201)

        response_after_create = self.client.get(self.products_url)

        self.assertEqual(response_after_create.status_code, 200)
        self.assertEqual(response_after_create["X-Cache"], "MISS")

        results = self.get_results(response_after_create)
        names = [item["name"] for item in results]

        self.assertIn("MacBook Pro", names)



    def test_product_list_response_is_cached_after_first_request(self):
        first_response = self.client.get(self.products_url)

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(first_response["X-Cache"], "MISS")

        second_response = self.client.get(self.products_url)

        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(second_response["X-Cache"], "HIT")



    def test_search_products_by_name(self):
        response = self.client.get(self.products_url, {"search": "iphone"})

        self.assertEqual(response.status_code, 200)

        results = self.get_results(response)
        names = [item["name"] for item in results]

        self.assertIn("iPhone 15", names)

    def test_product_list_cache_is_invalidated_when_admin_updates_product(self):
        first_response = self.client.get(self.products_url)
        self.assertEqual(first_response["X-Cache"], "MISS")

        second_response = self.client.get(self.products_url)
        self.assertEqual(second_response["X-Cache"], "HIT")

        self.client.force_authenticate(user=self.admin)

        product_detail_url = reverse("product-detail", args=[self.iphone.id])

        update_response = self.client.patch(
        product_detail_url,
        {
            "price": "1200.00"
        },
        format="json"
        )

        self.assertEqual(update_response.status_code, 200)

        self.iphone.refresh_from_db()
        self.assertEqual(self.iphone.price, Decimal("1200.00"))

        response_after_update = self.client.get(self.products_url)

        self.assertEqual(response_after_update.status_code, 200)
        self.assertEqual(response_after_update["X-Cache"], "MISS")


    def test_product_list_cache_is_invalidated_when_admin_deletes_product(self):
        first_response = self.client.get(self.products_url)
        self.assertEqual(first_response["X-Cache"], "MISS")

        second_response = self.client.get(self.products_url)
        self.assertEqual(second_response["X-Cache"], "HIT")

        self.client.force_authenticate(user=self.admin)

        product_detail_url = reverse("product-detail", args=[self.samsung.id])

        delete_response = self.client.delete(product_detail_url)

        self.assertEqual(delete_response.status_code, 204)

        response_after_delete = self.client.get(self.products_url)

        self.assertEqual(response_after_delete.status_code, 200)
        self.assertEqual(response_after_delete["X-Cache"], "MISS")

        results = self.get_results(response_after_delete)
        names = [item["name"] for item in results]

        self.assertNotIn("Samsung S24", names)


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
    def test_category_slug_is_generated_automatically(self):
        category = Category.objects.create(name="Home Appliances")

        self.assertEqual(category.slug, "home-appliances")


    def test_category_slug_is_unique_when_name_repeats(self):
        first_category = Category.objects.create(name="Accessories")
        second_category = Category.objects.create(name="Accessories")

        self.assertEqual(first_category.slug, "accessories")
        self.assertEqual(second_category.slug, "accessories-1")





class TestApi(APITestCase):
    def setUp(self):
        self.user=User.objects.create_user(
            username="ashraf",
            email="admin@admin.com",
            password="12341234",
            is_staff=True
        )



    def test_add_product(self):

        self.client.force_authenticate(user=self.user)
        category=Category.objects.create(
            name="phone"
        )

        data={

            "category":category.id,
            "name":"iphone-16",
            "price":50.00,
            "in_stock":2
        }

        response=self.client.post('/api/v1/products/product/',data)

        self.assertEqual(response.status_code,201)

        self.assertEqual(Product.objects.count(),1)
        
