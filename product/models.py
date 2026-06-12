from django.db import models
from io import BytesIO
from PIL import Image
from django.core.files import File
from django.core.exceptions import ValidationError
import uuid
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=225)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"/{self.slug}/"
    
    def save(self, *args, **kwargs):
        if not self.slug:
          base_slug = slugify(self.name) or str(uuid.uuid4())[:8]
          unique_slug = base_slug
          counter = 1

          while Category.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
              unique_slug = f"{base_slug}-{counter}"
              counter += 1

          self.slug = unique_slug

        super().save(*args, **kwargs)


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )
    name = models.CharField(max_length=225)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='uploads/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='uploads/', blank=True, null=True)
    in_stock = models.PositiveIntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_added']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['date_added']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(price__gte=0),
                name='price_gte_0'
            ),
            models.CheckConstraint(
                check=models.Q(in_stock__gte=0),
                name='stock_gte_0'
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    def get_absolute_url(self):
        return f"/{self.category.slug}/{self.slug}/"

    def get_image(self):
        if self.image:
            return self.image.url
        return ''

    @property
    def is_available(self):
        return self.in_stock > 0

    def clean(self):
        if self.price < 0:
            raise ValidationError("Price cannot be negative")
        if self.in_stock < 0:
            raise ValidationError("Stock cannot be negative")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) + "-" + str(uuid.uuid4())[:8]

        if self.image and not self.thumbnail:
            self.thumbnail = self.make_thumbnail(self.image)

        super().save(*args, **kwargs)

    def get_thumbnail(self):
        if self.thumbnail:
            return self.thumbnail.url
        return ''

    def make_thumbnail(self, image, size=(200, 300)):
        img = Image.open(image)
        img = img.convert('RGB')
        img.thumbnail(size)

        thumb_io = BytesIO()
        img.save(thumb_io, 'JPEG', quality=85)

        filename = f"{uuid.uuid4()}.jpg"
        return File(thumb_io, name=filename)