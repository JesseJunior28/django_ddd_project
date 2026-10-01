import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("product", "0002_product_catalog"), ("branch", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="BranchProductStock",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sku", models.IntegerField()),
                ("ean", models.CharField(max_length=64)),
                ("stock", models.IntegerField()),
                ("original_price", models.FloatField(blank=True, null=True)),
                ("discount_price", models.FloatField(blank=True, null=True)),
                ("branch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="product_stock", to="branch.branch")),
            ],
            options={"db_table": "branch_product_stocks"},
        ),
        migrations.AddConstraint(model_name="branchproductstock", constraint=models.UniqueConstraint(fields=("sku", "ean", "branch"), name="product_branch_stock_unique")),
    ]
