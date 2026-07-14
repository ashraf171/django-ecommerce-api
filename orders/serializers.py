from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_name",
            "price",
            "quantity",
            "total_price",
        ]

    def get_total_price(self, obj):
        return obj.price * obj.quantity


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(
        source="order_items",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "total_price",
            "payment_id",
            "paid_at",
            "created_at",
            "updated_at",
            "items",
        ]
        read_only_fields = [
            "id",
            "status",
            "total_price",
            "payment_id",
            "paid_at",
            "created_at",
            "updated_at",
            "items",
        ]