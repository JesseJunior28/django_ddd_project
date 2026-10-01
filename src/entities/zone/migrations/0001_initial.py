import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name="Zone", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("name", models.CharField(max_length=255)), ("hex_color", models.CharField(max_length=255)), ("is_marketing_zone", models.BooleanField(default=False))], options={"db_table": "zones"}),
        migrations.CreateModel(name="Department", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("name", models.CharField(max_length=255)), ("orientation", models.CharField(choices=[("ENTRY", "Entry"), ("COUNTER", "Counter"), ("LEFT_TO_RIGHT", "Left To Right")], max_length=20)), ("zone", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="departments", to="zone.zone"))], options={"db_table": "departments"}),
        migrations.CreateModel(name="Level", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("name", models.CharField(max_length=255)), ("label", models.CharField(blank=True, max_length=255, null=True)), ("hex_color", models.CharField(max_length=255)), ("divisions", django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), default=list, size=None)), ("department", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="levels", to="zone.department"))], options={"db_table": "levels"}),
    ]
