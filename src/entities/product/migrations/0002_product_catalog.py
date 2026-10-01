import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("product", "0001_initial"), ("industry", "0001_initial"), ("zone", "0001_initial")]
    operations = [
        migrations.AlterField(model_name="product", name="ean", field=models.CharField(max_length=64)),
        migrations.AlterField(model_name="product", name="length", field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name="product", name="sku", field=models.IntegerField(default=0)),
        migrations.AddField(model_name="product", name="primary_image_url", field=models.CharField(default="", max_length=1024)),
        migrations.AddField(model_name="product", name="secondary_image_url", field=models.CharField(blank=True, max_length=1024, null=True)),
        migrations.AddField(model_name="product", name="tertiary_image_url", field=models.CharField(blank=True, max_length=1024, null=True)),
        migrations.AddField(model_name="product", name="family", field=models.CharField(blank=True, max_length=255, null=True)),
        migrations.AddField(model_name="product", name="is_release", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="product", name="is_news", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="product", name="brand", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="products", to="industry.brand")),
        migrations.AddConstraint(model_name="product", constraint=models.UniqueConstraint(fields=("sku", "ean"), name="product_sku_ean_unique")),
        migrations.CreateModel(name="BaseProduct", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("sku", models.IntegerField()), ("ean", models.CharField(max_length=64)), ("name", models.CharField(max_length=255)), ("family", models.CharField(blank=True, max_length=255, null=True)), ("width", models.IntegerField(blank=True, null=True)), ("height", models.IntegerField(blank=True, null=True)), ("length", models.IntegerField(blank=True, null=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("brand", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="base_products", to="industry.brand"))], options={"db_table":"base_products"}),
        migrations.CreateModel(name="ProductExpositionDetail", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("forefront", models.IntegerField(default=1)), ("min_stock", models.IntegerField(default=1)), ("ranking", models.IntegerField()), ("priority", models.IntegerField()), ("fixed_side", models.CharField(choices=[("WIDTH","Width"),("HEIGHT","Height"),("LENGTH","Length")], max_length=6)), ("is_extra_exposition", models.BooleanField(default=False)), ("level", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="expositions_details", to="zone.level")), ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="expositions_details", to="product.product"))], options={"db_table":"product_exposition_details"}),
        migrations.AddConstraint(model_name="baseproduct", constraint=models.UniqueConstraint(fields=("sku", "ean"), name="base_product_sku_ean_unique")),
        migrations.AddConstraint(model_name="productexpositiondetail", constraint=models.UniqueConstraint(fields=("product", "level"), name="product_level_exposition_unique")),
    ]
