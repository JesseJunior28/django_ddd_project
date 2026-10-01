from django.db import models


class BranchLayout(models.Model):
    branch = models.OneToOneField("branch.Branch", related_name="layout", on_delete=models.PROTECT)
    version = models.IntegerField(default=1)
    version_code = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "branch_layout"


class LayoutElement(models.Model):
    class ElementType(models.TextChoices):
        BIG_BASKET = "BIG_BASKET"
        REFRIGERATOR = "REFRIGERATOR"
        FREEZER = "FREEZER"
        COUNTER = "COUNTER"
        CASHIER = "CASHIER"
        MODULE = "MODULE"
        WALL = "WALL"
        ENTRY = "ENTRY"
        LABEL = "LABEL"

    text = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=16, choices=ElementType.choices)
    branch_layout = models.ForeignKey(BranchLayout, related_name="elements", on_delete=models.CASCADE)

    class Meta:
        db_table = "layout_element"


class ElementModuleConfiguration(models.Model):
    class Orientation(models.TextChoices):
        LEFT_TO_RIGHT = "LEFT_TO_RIGHT"
        RIGHT_TO_LEFT = "RIGHT_TO_LEFT"

    class FrontDirection(models.TextChoices):
        UP = "UP"
        DOWN = "DOWN"
        LEFT = "LEFT"
        RIGHT = "RIGHT"

    layout_element = models.OneToOneField(LayoutElement, primary_key=True, related_name="module_configuration", on_delete=models.CASCADE)
    orientation = models.CharField(max_length=14, choices=Orientation.choices, null=True, blank=True)
    front_direction = models.CharField(max_length=5, choices=FrontDirection.choices, null=True, blank=True)
    is_marketing_point = models.BooleanField(default=False)
    module = models.ForeignKey("planogram.Module", related_name="element_module_configurations", null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        db_table = "element_module_configuration"
        constraints = [models.UniqueConstraint(fields=["layout_element", "module"], name="layout_element_module_unique")]


class RectElement(models.Model):
    layout_element = models.OneToOneField(LayoutElement, primary_key=True, related_name="rect_element", on_delete=models.CASCADE)
    position_x = models.FloatField()
    position_y = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    rotation = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "rect_element"


class LineElement(models.Model):
    layout_element = models.OneToOneField(LayoutElement, primary_key=True, related_name="line_element", on_delete=models.CASCADE)
    x1 = models.FloatField()
    y1 = models.FloatField()
    x2 = models.FloatField()
    y2 = models.FloatField()

    class Meta:
        db_table = "line_element"
