from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Industry",
            fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("name", models.CharField(max_length=255))],
            options={"db_table": "industries"},
        ),
        migrations.CreateModel(
            name="Brand",
            fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("name", models.CharField(max_length=255)), ("industry", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="brands", to="industry.industry"))],
            options={"db_table": "brands"},
        ),
    ]
