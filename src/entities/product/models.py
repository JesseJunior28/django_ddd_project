from django.db import models


class Product(models.Model):

    sku = models.IntegerField(default=0)
    ean = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    primary_image_url = models.CharField(max_length=1024, default="")
    secondary_image_url = models.CharField(max_length=1024, null=True, blank=True)
    tertiary_image_url = models.CharField(max_length=1024, null=True, blank=True)
    family = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_release = models.BooleanField(default=False)
    is_news = models.BooleanField(default=False)
    width = models.FloatField()
    height = models.FloatField()
    length = models.FloatField(null=True, blank=True)
    brand = models.ForeignKey("industry.Brand", related_name="products", on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["sku", "ean"], name="product_sku_ean_unique")]

    def __str__(self):
        return self.name


class BaseProduct(models.Model):
    sku = models.IntegerField()
    ean = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    family = models.CharField(max_length=255, null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    length = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    brand = models.ForeignKey("industry.Brand", related_name="base_products", on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        db_table = "base_products"
        constraints = [models.UniqueConstraint(fields=["sku", "ean"], name="base_product_sku_ean_unique")]


class ProductExpositionDetail(models.Model):
    class FixedSide(models.TextChoices):
        WIDTH = "WIDTH"
        HEIGHT = "HEIGHT"
        LENGTH = "LENGTH"
    product = models.ForeignKey(Product, related_name="expositions_details", on_delete=models.PROTECT)
    level = models.ForeignKey("zone.Level", related_name="expositions_details", on_delete=models.PROTECT)
    forefront = models.IntegerField(default=1)
    min_stock = models.IntegerField(default=1)
    ranking = models.IntegerField()
    priority = models.IntegerField()
    fixed_side = models.CharField(max_length=6, choices=FixedSide.choices)
    is_extra_exposition = models.BooleanField(default=False)

    class Meta:
        db_table = "product_exposition_details"
        constraints = [models.UniqueConstraint(fields=["product", "level"], name="product_level_exposition_unique")]


class BranchProductStock(models.Model):
    """Stock imported for a product identity in one branch.

    O ORM não expressa diretamente a chave estrangeira composta para Product;
    the matching `(sku, ean)` identity and its uniqueness are retained here.
    """
    sku = models.IntegerField()
    ean = models.CharField(max_length=64)
    branch = models.ForeignKey("branch.Branch", related_name="product_stock", on_delete=models.PROTECT)
    stock = models.IntegerField()
    original_price = models.FloatField(null=True, blank=True)
    discount_price = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "branch_product_stocks"
        constraints = [models.UniqueConstraint(fields=["sku", "ean", "branch"], name="product_branch_stock_unique")]
