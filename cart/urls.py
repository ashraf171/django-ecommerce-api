from django.urls import path
from .views import CartView,CartItemView,CartClearView


urlpatterns=[
    path('',CartView.as_view(),name='cart-detail'),
    path('item/',CartItemView.as_view(),name='cart-item'),
    path('clear/', CartClearView.as_view(), name='cart-clear')
]