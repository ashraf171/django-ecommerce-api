from rest_framework import serializers
from .models import Category,Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields=['id','name','slug']
        read_only_fields=['id','slug']



class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True
    )
    category_detail = CategorySerializer(source='category', read_only=True)

    thumbnail = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'category_detail',
            'name', 'slug', 'description',
            'price', 'image', 'thumbnail',
            'in_stock', 'date_added', 'is_available'
        ]
        read_only_fields = ['id', 'slug', 'date_added', 'is_available']


    def get_thumbnail(self, obj):
        return obj.get_thumbnail()

    def get_image(self, obj):
        return obj.get_image()