from django.db import models
from django.contrib.auth.models import User
from product.models import Product
from django.core.exceptions import ValidationError
from django.conf import settings

class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total_price(self):
        return sum(item.subtotal() for item in self.items.all())

    def __str__(self):
        return f"Cart of: {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'],
                name='unique_cart_product'
            )
        ]

    def subtotal(self):
        return self.price * self.quantity

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")

        if self.product and self.quantity > self.product.in_stock:
            raise ValidationError("Not enough stock available")

    def save(self, *args, **kwargs):
        
        if not self.price:
            self.price = self.product.price

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"