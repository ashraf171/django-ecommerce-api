from rest_framework.routers import DefaultRouter
from product.views import ProductViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'product', ProductViewSet,basename='product')
router.register(r'categories', CategoryViewSet,basename='categories')

urlpatterns = router.urls