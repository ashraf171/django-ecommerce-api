from decimal import Decimal
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.exceptions import ValidationError
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem, Status
from cart.services import checkout
from product.models import Category, Product
from django.urls import reverse

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
        
    def test_checkout_fails_when_cart_does_not_exist(self):
        user_without_cart = get_user_model().objects.create_user(
            username="no_cart_user",
            email="no_cart@example.com",
            password="testpass123"
        )

        with self.assertRaises(ValidationError) as context:
            checkout(user_without_cart)

        self.assertIn("Cart not found", str(context.exception))


    def test_checkout_creates_order_and_order_item(self):
        order = checkout(self.user)

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, Status.PENDING)
        self.assertEqual(order.total_price, Decimal("200.00"))
    
    def test_api_checkout_creates_order_decreases_stock_and_clears_cart(self):
        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.post("/api/v1/orders/checkout/")

        self.assertEqual(response.status_code, 201)

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

        order = Order.objects.first()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, Status.PENDING)
        self.assertEqual(order.total_price, Decimal("200.00"))

        order_item = OrderItem.objects.first()
        self.assertEqual(order_item.order, order)
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.price, Decimal("100.00"))
        self.assertEqual(order_item.product_name, self.product.name)

        self.product.refresh_from_db()
        self.assertEqual(self.product.in_stock, 8)

        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 0)
    

    def test_api_checkout_fails_when_cart_is_empty(self):
        client = APIClient()
        client.force_authenticate(user=self.user)

        CartItem.objects.filter(cart=self.cart).delete()

        response = client.post("/api/v1/orders/checkout/")

        self.assertEqual(response.status_code, 400)

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)

        self.product.refresh_from_db()
        self.assertEqual(self.product.in_stock, 10)
    

    def test_api_checkout_fails_when_stock_is_insufficient(self):
        client = APIClient()
        client.force_authenticate(user=self.user)

        self.cart_item.quantity = 20
        self.cart_item.save()

        response = client.post("/api/v1/orders/checkout/")

        self.assertEqual(response.status_code, 400)

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)

        self.product.refresh_from_db()
        self.assertEqual(self.product.in_stock, 10)

        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 1)

    def test_unauthenticated_user_cannot_checkout(self):
        client = APIClient()

        response = client.post("/api/v1/orders/checkout/")

        self.assertEqual(response.status_code, 401)

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)

        self.product.refresh_from_db()
        self.assertEqual(self.product.in_stock, 10)

        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 1)

    def test_user_can_list_only_own_orders(self):
        own_order = checkout(self.user)

        other_user = User.objects.create_user(
        username="otheruser",
        email="other@example.com",
        password="testpass123",
        )

        other_cart = Cart.objects.create(user=other_user)

        CartItem.objects.create(
        cart=other_cart,
        product=self.product,
        quantity=1,
        price=self.product.price,
        )

        other_order = checkout(other_user)

        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.get("/api/v1/orders/")

        self.assertEqual(response.status_code, 200)

        results = (
        response.data["results"]
        if isinstance(response.data, dict) and "results" in response.data
        else response.data
        )

        order_ids = [order["id"] for order in results]

        self.assertIn(own_order.id, order_ids)
        self.assertNotIn(other_order.id, order_ids)
    def test_user_cannot_retrieve_another_users_order(self):
        other_user = User.objects.create_user(
        username="otheruser2",
        email="other2@example.com",
        password="testpass123",
        )

        other_cart = Cart.objects.create(user=other_user)

        CartItem.objects.create(
        cart=other_cart,
        product=self.product,
        quantity=1,
        price=self.product.price,
        )

        other_order = checkout(other_user)

        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.get(f"/api/v1/orders/{other_order.id}/")

        self.assertEqual(response.status_code, 404)


    def test_user_can_pay_pending_order(self):
        order = checkout(self.user)

        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.post(f"/api/v1/orders/{order.id}/pay/")

        self.assertEqual(response.status_code, 200)

        order.refresh_from_db()

        self.assertEqual(order.status, Status.PAID)
        self.assertIsNotNone(order.payment_id)
        self.assertIsNotNone(order.paid_at)

        self.assertEqual(response.data["detail"], "Payment successful")
        self.assertEqual(response.data["order_id"], order.id)
        self.assertEqual(response.data["status"], Status.PAID)


        
    def test_user_cannot_pay_already_paid_order(self):
        order = checkout(self.user)

        client = APIClient()
        client.force_authenticate(user=self.user)

        first_response = client.post(f"/api/v1/orders/{order.id}/pay/")

        self.assertEqual(first_response.status_code, 200)

        order.refresh_from_db()

        old_payment_id = order.payment_id
        old_paid_at = order.paid_at

        second_response = client.post(f"/api/v1/orders/{order.id}/pay/")

        self.assertEqual(second_response.status_code, 400)

        order.refresh_from_db()

        self.assertEqual(order.status, Status.PAID)
        self.assertEqual(order.payment_id, old_payment_id)
        self.assertEqual(order.paid_at, old_paid_at)
        self.assertEqual(
        second_response.data["detail"],
        "Only PENDING orders can be paid. Current status is PAID"
        )   


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


    def test_user_cannot_pay_another_users_order(self):
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123"
        )

        order = Order.objects.create(
            user=self.user,
            total_price=Decimal("100.00")
        )

        client = APIClient()
        client.force_authenticate(user=other_user)

        response = client.post(f"/api/v1/orders/{order.id}/pay/")

        self.assertIn(response.status_code, [403, 404])

        order.refresh_from_db()
        self.assertEqual(order.status, Status.PENDING)
        self.assertIsNone(order.payment_id)
        self.assertIsNone(order.paid_at)
    



    def test_admin_can_list_all_orders(self):
        other_user = User.objects.create_user(
            username="otheruser2",
            email="other2@example.com",
            password="testpass123"
        )

        admin_user = User.objects.create_superuser(
            username="orderadmin",
            email="orderadmin@example.com",
            password="adminpass123"
        )

        first_order = Order.objects.create(
            user=self.user,
            total_price=Decimal("100.00")
        )

        second_order = Order.objects.create(
            user=other_user,
            total_price=Decimal("200.00")
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.get("/api/v1/orders/")

        self.assertEqual(response.status_code, 200)

        data = response.data

        if isinstance(data, dict) and "results" in data:
            results = data["results"]
        else:
            results = data

        order_ids = [item["id"] for item in results]

        self.assertIn(first_order.id, order_ids)
        self.assertIn(second_order.id, order_ids)