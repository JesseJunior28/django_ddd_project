from django.db import models


class Planogram(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    department = models.ForeignKey("zone.Department", related_name="planograms", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "planograms"


class Module(models.Model):
    sequence = models.IntegerField()
    width = models.IntegerField(default=100)
    planogram = models.ForeignKey(Planogram, related_name="modules", on_delete=models.PROTECT)

    class Meta:
        db_table = "modules"
        constraints = [models.UniqueConstraint(fields=["sequence", "planogram"], name="module_sequence_planogram_unique")]


class Shelf(models.Model):
    sequence = models.IntegerField()
    module = models.ForeignKey(Module, related_name="shelves", on_delete=models.PROTECT)

    class Meta:
        db_table = "shelves"
        constraints = [models.UniqueConstraint(fields=["sequence", "module"], name="shelf_sequence_module_unique")]


class ShelfLevel(models.Model):
    class ExpositionType(models.TextChoices):
        SHELF = "SHELF"
        BASCKET = "BASCKET"
        BAR = "BAR"

    width = models.IntegerField(default=100)
    sequence = models.IntegerField()
    exposition_type = models.CharField(max_length=7, choices=ExpositionType.choices)
    level = models.ForeignKey("zone.Level", related_name="shelf_levels", on_delete=models.PROTECT)
    shelf = models.ForeignKey(Shelf, related_name="levels", on_delete=models.PROTECT)

    class Meta:
        db_table = "shelf_levels"
        constraints = [models.UniqueConstraint(fields=["sequence", "shelf"], name="shelf_level_sequence_shelf_unique")]
