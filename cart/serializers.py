from rest_framework import serializers
from .models import Cart, CartItem
from product.serializers import ProductSerializer
from decimal import Decimal


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    sub_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'sub_total']

    def get_sub_total(self, obj):
        
       total=obj.price * obj.quantity
       return str(total.quantize(Decimal('0.01')))


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price'] 

    
    def get_total_price(self, obj):
        total = sum(
        (item.product.price * item.quantity for item in obj.items.all()),
        Decimal('0.00') 
         )
        return str(total.quantize(Decimal('0.01')))