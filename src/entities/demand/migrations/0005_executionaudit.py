import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('demand', '0004_alter_executionoccurrence_status'), ('product', '0003_branch_product_stock')]
    operations = [migrations.CreateModel(name='ExecutionAudit', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('current_stock', models.IntegerField()), ('is_exposed', models.BooleanField(blank=True, null=True)),
        ('is_position_acceptable', models.BooleanField(blank=True, null=True)),
        ('non_exposition_reason', models.CharField(blank=True, max_length=32, null=True)),
        ('execution', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='audits', to='demand.execution')),
        ('product_exposition', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='execution_audits', to='product.productexpositiondetail')),
    ], options={'db_table': 'execution_audit'})]
