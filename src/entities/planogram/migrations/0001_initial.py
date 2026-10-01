import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("zone", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Planogram",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(blank=True, max_length=255, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("department", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="planograms", to="zone.department")),
            ],
            options={"db_table": "planograms"},
        ),
        migrations.CreateModel(
            name="Module",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sequence", models.IntegerField()),
                ("width", models.IntegerField(default=100)),
                ("planogram", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="modules", to="planogram.planogram")),
            ],
            options={"db_table": "modules"},
        ),
        migrations.CreateModel(
            name="Shelf",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sequence", models.IntegerField()),
                ("module", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="shelves", to="planogram.module")),
            ],
            options={"db_table": "shelves"},
        ),
        migrations.CreateModel(
            name="ShelfLevel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("width", models.IntegerField(default=100)),
                ("sequence", models.IntegerField()),
                ("exposition_type", models.CharField(choices=[("SHELF", "Shelf"), ("BASCKET", "Bascket"), ("BAR", "Bar")], max_length=7)),
                ("level", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="shelf_levels", to="zone.level")),
                ("shelf", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="levels", to="planogram.shelf")),
            ],
            options={"db_table": "shelf_levels"},
        ),
        migrations.AddConstraint(model_name="module", constraint=models.UniqueConstraint(fields=("sequence", "planogram"), name="module_sequence_planogram_unique")),
        migrations.AddConstraint(model_name="shelf", constraint=models.UniqueConstraint(fields=("sequence", "module"), name="shelf_sequence_module_unique")),
        migrations.AddConstraint(model_name="shelflevel", constraint=models.UniqueConstraint(fields=("sequence", "shelf"), name="shelf_level_sequence_shelf_unique")),
    ]
