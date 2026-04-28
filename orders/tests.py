from decimal import Decimal
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.exceptions import ValidationError
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem, Status
from cart.services import checkout
from product.models import Category, Product


User = get_user_model()


class CheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

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

        self.cart = Cart.objects.create(user=self.user)

        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
            price=self.product.price
        )

    def test_checkout_creates_order_and_order_item(self):
        order = checkout(self.user)

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, Status.PENDING)
        self.assertEqual(order.total_price, Decimal("200.00"))

    def test_checkout_decreases_product_stock(self):
        checkout(self.user)

        self.product.refresh_from_db()

        self.assertEqual(self.product.in_stock, 8)

    def test_checkout_clears_cart(self):
        checkout(self.user)

        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 0)
    def test_checkout_fails_when_cart_is_empty(self):
        self.cart.items.all().delete()

        with self.assertRaises(ValidationError):
            checkout(self.user)

        self.assertEqual(Order.objects.count(), 0)


    def test_checkout_fails_when_quantity_is_greater_than_stock(self):
        self.cart_item.quantity = 20
        self.cart_item.save(update_fields=["quantity"])

        with self.assertRaises(ValidationError):
            checkout(self.user)

        self.product.refresh_from_db()

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(self.product.in_stock, 10)
    
    def test_admin_can_cancel_order_and_restore_stock(self):
        admin = User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123"
    )

        order = checkout(self.user)

        client = APIClient()
        client.force_authenticate(user=admin)

        response = client.patch(
        f"/api/v1/orders/{order.id}/change_status/",
        {"status": Status.CANCELED},
        format="json"
        )

        self.assertEqual(response.status_code, 200)

        order.refresh_from_db()
        self.product.refresh_from_db()

        self.assertEqual(order.status, Status.CANCELED)
        self.assertEqual(self.product.in_stock, 10)


    def test_normal_user_cannot_change_order_status(self):
        order = checkout(self.user)

        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.patch(
        f"/api/v1/orders/{order.id}/change_status/",
        {"status": Status.CANCELED},
        format="json"
        )

        self.assertEqual(response.status_code, 403)


    def test_invalid_status_transition_is_rejected(self):
        admin = User.objects.create_superuser(
        username="admin2",
        email="admin2@example.com",
        password="adminpass123"
        )

        order = checkout(self.user)

        client = APIClient()
        client.force_authenticate(user=admin)

        response = client.patch(
        f"/api/v1/orders/{order.id}/change_status/",
        {"status": Status.DELIVERED},
        format="json"
        )

        self.assertEqual(response.status_code, 400)

        order.refresh_from_db()

        self.assertEqual(order.status, Status.PENDING)