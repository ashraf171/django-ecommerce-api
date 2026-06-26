from celery import shared_task

from orders.models import Order



@shared_task(ignore_result=True)
def fake_order_confirmation_task(order_id):
    order = Order.objects.select_related("user").get(id=order_id)

    print(
        f"Fake order confirmation sent for order #{order.id} "
        f"for user #{order.user_id}. Total: {order.total_price}"
    )

    return f"Fake confirmation sent for order #{order.id}"