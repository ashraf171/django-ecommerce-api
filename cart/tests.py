from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from cart.models import Cart, CartItem
from product.models import Category, Product


User = get_user_model()


class CartTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics"
        )

        self.product = Product.objects.create(
            category=self.category,
            name="iPhone 15",
            description="Test product",
            price=Decimal("100.00"),
            in_stock=10
        )

        self.out_of_stock_product = Product.objects.create(
            category=self.category,
            name="Old Phone",
            description="Out of stock product",
            price=Decimal("50.00"),
            in_stock=0
        )

        self.cart, _ = Cart.objects.get_or_create(user=self.user)

    def test_add_item_to_cart(self):
        response = self.client.post(
            "/api/v1/cart/item/",
            {
                "product_id": self.product.id,
                "quantity": 2
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(CartItem.objects.count(), 1)

        cart_item = CartItem.objects.first()

        self.assertEqual(cart_item.cart, self.cart)
        self.assertEqual(cart_item.product, self.product)
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(cart_item.price, self.product.price)

    def test_add_same_item_increases_quantity(self):
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
            price=self.product.price
        )

        response = self.client.post(
            "/api/v1/cart/item/",
            {
                "product_id": self.product.id,
                "quantity": 3
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        cart_item = CartItem.objects.get(cart=self.cart, product=self.product)

        self.assertEqual(cart_item.quantity, 5)

    def test_cannot_add_quantity_greater_than_stock(self):
        response = self.client.post(
            "/api/v1/cart/item/",
            {
                "product_id": self.product.id,
                "quantity": 20
            },
            format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(CartItem.objects.count(), 0)
        self.assertIn("detail", response.data)

    def test_cannot_add_out_of_stock_product(self):
        response = self.client.post(
            "/api/v1/cart/item/",
            {
                "product_id": self.out_of_stock_product.id,
                "quantity": 1
            },
            format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(CartItem.objects.count(), 0)
        self.assertEqual(response.data["detail"], "Product is out of stock")

    def test_update_cart_item_quantity(self):
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
            price=self.product.price
        )

        response = self.client.put(
            "/api/v1/cart/item/",
            {
                "product_id": self.product.id,
                "quantity": 5
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        cart_item = CartItem.objects.get(cart=self.cart, product=self.product)

        self.assertEqual(cart_item.quantity, 5)

    def test_update_quantity_to_zero_deletes_item(self):
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
            price=self.product.price
        )

        response = self.client.put(
            "/api/v1/cart/item/",
            {
                "product_id": self.product.id,
                "quantity": 0
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_cannot_update_quantity_greater_than_stock(self):
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
            price=self.product.price
        )

        response = self.client.put(
            "/api/v1/cart/item/",
            {
                "product_id": self.product.id,
                "quantity": 20
            },
            format="json"
        )

        self.assertEqual(response.status_code, 400)

        cart_item = CartItem.objects.get(cart=self.cart, product=self.product)

        self.assertEqual(cart_item.quantity, 2)
        self.assertIn("detail", response.data)

    def test_delete_cart_item(self):
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
            price=self.product.price
        )

        response = self.client.delete(
            "/api/v1/cart/item/",
            {
                "product_id": self.product.id
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CartItem.objects.count(), 0)
        self.assertEqual(response.data["detail"], "Item removed")

    def test_delete_item_not_found_returns_404(self):
        response = self.client.delete(
            "/api/v1/cart/item/",
            {
                "product_id": self.product.id
            },
            format="json"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "Item not found in cart")

    def test_clear_cart(self):
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
            price=self.product.price
        )

        response = self.client.post(
            "/api/v1/cart/clear/",
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CartItem.objects.count(), 0)
        self.assertEqual(response.data["detail"], "Cart cleared successfully")
    

    def test_cart_total_uses_cart_item_snapshot_price(self):
        CartItem.objects.create(
        cart=self.cart,
        product=self.product,
        quantity=2,
        price=Decimal("80.00")
    )

        self.product.price = Decimal("120.00")
        self.product.save()

        response = self.client.get("/api/v1/cart/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_price"], "160.00")