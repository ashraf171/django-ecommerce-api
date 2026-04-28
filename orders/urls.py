from django.urls import path 
from .views import CheckoutView,OrderViewSet
from rest_framework.routers import DefaultRouter 

router=DefaultRouter()
router.register('',OrderViewSet,basename='orders')

urlpatterns=[
    path('checkout/',CheckoutView.as_view(),name='checkout'),
    
]

urlpatterns+=router.urls