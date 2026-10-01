import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("branch", "0001_initial"), ("planogram", "0001_initial")]
    operations = [
        migrations.CreateModel(name="BranchLayout", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("version", models.IntegerField(default=1)), ("version_code", models.UUIDField(blank=True, null=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("branch", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="layout", to="branch.branch")),
        ], options={"db_table": "branch_layout"}),
        migrations.CreateModel(name="LayoutElement", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("text", models.CharField(blank=True, max_length=255, null=True)),
            ("type", models.CharField(choices=[("BIG_BASKET", "Big Basket"), ("REFRIGERATOR", "Refrigerator"), ("FREEZER", "Freezer"), ("COUNTER", "Counter"), ("CASHIER", "Cashier"), ("MODULE", "Module"), ("WALL", "Wall"), ("ENTRY", "Entry"), ("LABEL", "Label")], max_length=16)),
            ("branch_layout", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="elements", to="branch_layout.branchlayout")),
        ], options={"db_table": "layout_element"}),
        migrations.CreateModel(name="LineElement", fields=[
            ("layout_element", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name="line_element", serialize=False, to="branch_layout.layoutelement")),
            ("x1", models.FloatField()), ("y1", models.FloatField()), ("x2", models.FloatField()), ("y2", models.FloatField()),
        ], options={"db_table": "line_element"}),
        migrations.CreateModel(name="RectElement", fields=[
            ("layout_element", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name="rect_element", serialize=False, to="branch_layout.layoutelement")),
            ("position_x", models.FloatField()), ("position_y", models.FloatField()), ("width", models.FloatField()), ("height", models.FloatField()), ("rotation", models.IntegerField(blank=True, null=True)),
        ], options={"db_table": "rect_element"}),
        migrations.CreateModel(name="ElementModuleConfiguration", fields=[
            ("layout_element", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name="module_configuration", serialize=False, to="branch_layout.layoutelement")),
            ("orientation", models.CharField(blank=True, choices=[("LEFT_TO_RIGHT", "Left To Right"), ("RIGHT_TO_LEFT", "Right To Left")], max_length=14, null=True)),
            ("front_direction", models.CharField(blank=True, choices=[("UP", "Up"), ("DOWN", "Down"), ("LEFT", "Left"), ("RIGHT", "Right")], max_length=5, null=True)),
            ("is_marketing_point", models.BooleanField(default=False)),
            ("module", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="element_module_configurations", to="planogram.module")),
        ], options={"db_table": "element_module_configuration"}),
        migrations.AddConstraint(model_name="elementmoduleconfiguration", constraint=models.UniqueConstraint(fields=("layout_element", "module"), name="layout_element_module_unique")),
    ]
