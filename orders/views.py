from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from .serializers import OrderSerializer
from cart.services import checkout
from rest_framework.permissions import IsAuthenticated
from .models import Order,Status

from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from django.db import transaction
from django.db.models import F
from product.models import Product
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework import mixins
import uuid
from django.utils import timezone

class Pagination(PageNumberPagination):
    page_size=10

class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    throttle_scope = "checkout"


    def post(self, request):
        try:
            order = checkout(request.user)
        except ValidationError as e:
            return Response(
                {"detail": e.messages[0] if hasattr(e, "messages") else str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    
class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = Pagination

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'total_price']
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()

        user = self.request.user
        queryset = Order.objects.prefetch_related("order_items")

        if user.is_staff:
            return queryset.all()

        return queryset.filter(user=user)

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        with transaction.atomic():
            order = (
                self.get_queryset()
                .select_for_update()
                .get(pk=pk)
            )

            if order.status != Status.PENDING:
                return Response(
                    {
                        "detail": f"Only PENDING orders can be paid. Current status is {order.status}"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            order.status = Status.PAID
            order.paid_at = timezone.now()
            order.payment_id = f"fake_payment_{uuid.uuid4().hex[:12]}"

            order.save(update_fields=["status", "paid_at", "payment_id", "updated_at"])

        return Response(
            {
                "detail": "Payment successful",
                "order_id": order.id,
                "status": order.status,
                "payment_id": order.payment_id,
                "paid_at": order.paid_at,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['patch'])
    def change_status(self, request, pk=None):
        user = request.user

        if not user.is_staff:
            return Response(
                {"detail": "You do not have permission to change order status"},
                status=status.HTTP_403_FORBIDDEN
            )

        new_status = request.data.get('status')

        if not new_status:
            return Response(
                {"detail": "status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_status not in Status.values:
            return Response(
                {"detail": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
            )

        allowed_transitions = {
            Status.PENDING: [Status.PAID, Status.CANCELED],
            Status.PAID: [Status.SHIPPED, Status.CANCELED],
            Status.SHIPPED: [Status.DELIVERED],
            Status.DELIVERED: [],
            Status.CANCELED: [],
            Status.FAILED: [Status.PENDING],
        }

        with transaction.atomic():
            order = (
                self.get_queryset()
                .select_for_update()
                .get(pk=pk)
            )

            current_status = order.status

            if new_status not in allowed_transitions.get(current_status, []):
                return Response(
                    {
                        "detail": f"Cannot change status from {current_status} to {new_status}"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if new_status == Status.CANCELED:
                order_items = order.order_items.select_related("product").all()

                for item in order_items:
                    Product.objects.filter(id=item.product_id).update(
                        in_stock=F("in_stock") + item.quantity
                    )

            order.status = new_status
            order.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "detail": "Order status updated successfully",
                "status": order.status
            },
            status=status.HTTP_200_OK
        )