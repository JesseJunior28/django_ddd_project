from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "ean", "name", "is_active", "width", "height", "length")
    search_fields = ("ean", "name")
    list_filter = ("is_active",)