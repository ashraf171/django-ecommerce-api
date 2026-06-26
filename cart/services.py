from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from orders.tasks import fake_order_confirmation_task
from cart.models import CartItem
from orders.models import Order, OrderItem, Status
from product.models import Product


def checkout(user):
    with transaction.atomic():
        try:
            cart = user.cart
        except Exception:
            raise ValidationError("Cart not found")

        items = (
            CartItem.objects
            .select_for_update()
            .select_related("product")
            .filter(cart=cart)
        )

        if not items.exists():
            raise ValidationError("Cart must not be empty")

        product_ids = [item.product_id for item in items]

        products = {
            product.id: product
            for product in Product.objects.select_for_update().filter(id__in=product_ids)
        }

        total_price = Decimal("0.00")

        for item in items:
            product = products[item.product_id]

            if item.quantity > product.in_stock:
                raise ValidationError(
                    f"Not enough stock for {product.name}. Available: {product.in_stock}"
                )

            total_price += item.quantity * item.price

        order = Order.objects.create(
            user=user,
            status=Status.PENDING,
            total_price=total_price
        )

        order_items = []

        for item in items:
            product = products[item.product_id]

            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    price=item.price,
                    product_name=product.name
                )
            )

            Product.objects.filter(id=product.id).update(
                in_stock=F("in_stock") - item.quantity
            )

        OrderItem.objects.bulk_create(order_items)

        items.delete()

        
        order_id = order.id
        transaction.on_commit(
        lambda: fake_order_confirmation_task.delay(order_id)
        )

        return order