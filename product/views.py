from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from product.models import Product, Category
from product.serializers import ProductSerializer, CategorySerializer
import django_filters
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import hashlib

from django.core.cache import cache
from rest_framework.response import Response


PRODUCT_LIST_CACHE_TIMEOUT = 60 * 5  # 5 minutes
PRODUCT_LIST_CACHE_VERSION_KEY = "products:list:version"


def get_product_list_cache_version():
    version = cache.get(PRODUCT_LIST_CACHE_VERSION_KEY)

    if version is None:
        version = 1
        cache.set(PRODUCT_LIST_CACHE_VERSION_KEY, version, timeout=None)

    return version


def bump_product_list_cache_version():
    try:
        cache.incr(PRODUCT_LIST_CACHE_VERSION_KEY)
    except ValueError:
        cache.set(PRODUCT_LIST_CACHE_VERSION_KEY, 2, timeout=None)



class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.CharFilter(field_name='category__slug')
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'category', 'name']



class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category').all().order_by('date_added')
    serializer_class = ProductSerializer
    filterset_class = ProductFilter

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    search_fields = ['name', 'description']
    ordering_fields = ['price', 'date_added', 'name']
    ordering = ['-date_added']



    def get_throttles(self):
        if self.action == "list":
            self.throttle_scope = "product_list"

        return super().get_throttles()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAdminUser()]

    def _get_product_list_cache_version(self):
        return get_product_list_cache_version()

    def _bump_product_list_cache_version(self):
        bump_product_list_cache_version()
    
    
    
    def list(self, request, *args, **kwargs):
        cache_version = self._get_product_list_cache_version()

        raw_cache_key = f"v{cache_version}:{request.get_full_path()}"
        key_hash = hashlib.md5(raw_cache_key.encode()).hexdigest()
        cache_key = f"products:list:v{cache_version}:{key_hash}"

        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data, headers={"X-Cache": "HIT"})

        response = super().list(request, *args, **kwargs)

        cache.set(
            cache_key,
            response.data,
            timeout=PRODUCT_LIST_CACHE_TIMEOUT
        )

        response["X-Cache"] = "MISS"
        return response

    def perform_create(self, serializer):
        serializer.save()
        self._bump_product_list_cache_version()

    def perform_update(self, serializer):
        serializer.save()
        self._bump_product_list_cache_version()

    def perform_destroy(self, instance):
        instance.delete()
        self._bump_product_list_cache_version()


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAdminUser()]
    
    def perform_update(self, serializer):
        serializer.save()
        bump_product_list_cache_version()

    def perform_destroy(self, instance):
        instance.delete()
        bump_product_list_cache_version()