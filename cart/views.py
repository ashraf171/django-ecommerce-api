from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Cart, CartItem
from product.models import Product
from .serializers import CartItemSerializer,CartSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated




class CartView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer
    def get(self, request):
        user = request.user

        cart, _ = Cart.objects.get_or_create(user=user)

        cart = Cart.objects.prefetch_related('items__product').get(id=cart.id)

        serializer = CartSerializer(cart)

        return Response(serializer.data)


class CartItemView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemSerializer

    def post(self, request):
        user = request.user
        cart, _ = Cart.objects.get_or_create(user=user)

        product_id = request.data.get('product_id')

        if not product_id:
            return Response(
                {'detail': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(request.data.get('quantity', 1))
        except (TypeError, ValueError):
            return Response(
                {'detail': 'Quantity must be a number'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity < 1:
            return Response(
                {'detail': 'Quantity must be at least 1'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'detail': 'Product Not Found'},
                status=status.HTTP_404_NOT_FOUND
            )
        if product.in_stock <= 0:
            return Response(
                {"detail": "Product is out of stock"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity > product.in_stock:
            return Response(
                {'detail': f'Only {product.in_stock} items available in stock'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                'quantity': quantity,
                'price': product.price
            }
        )

        if not created:
            requested_quantity = cart_item.quantity + quantity

            if requested_quantity > product.in_stock:
                return Response(
                    {'detail': f'Only {product.in_stock} items available in stock'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart_item.quantity = requested_quantity
            cart_item.save(update_fields=['quantity'])

        items = cart.items.select_related('product')
        serializer = CartItemSerializer(items, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    def put(self, request):
        user = request.user
        cart, _ = Cart.objects.get_or_create(user=user)

        product_id = request.data.get('product_id')

        if not product_id:
            return Response(
                {'detail': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'detail': 'Product Not Found'},
                status=status.HTTP_404_NOT_FOUND
            )
        if product.in_stock <= 0:
            return Response(
                {"detail": "Product is out of stock"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cart_item = CartItem.objects.get(cart=cart, product=product)
        except CartItem.DoesNotExist:
            return Response(
                {'detail': 'Item not found in cart'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            quantity = int(request.data.get('quantity'))
        except (TypeError, ValueError):
            return Response(
                {'detail': 'Quantity must be a number'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity < 0:
            return Response(
                {'detail': 'Quantity cannot be negative'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity == 0:
            cart_item.delete()
        else:
            if quantity > product.in_stock:
                return Response(
                    {'detail': f'Only {product.in_stock} items available in stock'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart_item.quantity = quantity
            cart_item.save(update_fields=['quantity'])

        items = cart.items.select_related('product')
        serializer = CartItemSerializer(items, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user
        cart, _ = Cart.objects.get_or_create(user=user)

        product_id = request.data.get('product_id')

        if not product_id:
            return Response(
                {'detail': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted, _ = CartItem.objects.filter(cart=cart, product_id=product_id).delete()

        if deleted == 0:
            return Response(
                {"detail": "Item not found in cart"},
                status=status.HTTP_404_NOT_FOUND
            )


        return Response(
            {"detail": "Item removed"},
            status=status.HTTP_200_OK
        )


class CartClearView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer

    def post(self, request):
        user = request.user

        cart, _ = Cart.objects.get_or_create(user=user)

        CartItem.objects.filter(cart=cart).delete()

        return Response(
            {"detail": "Cart cleared successfully"},
            status=status.HTTP_200_OK
        )