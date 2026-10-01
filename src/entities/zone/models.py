from django.contrib.postgres.fields import ArrayField
from django.db import models


class Zone(models.Model):
    name = models.CharField(max_length=255)
    hex_color = models.CharField(max_length=255)
    is_marketing_zone = models.BooleanField(default=False)

    class Meta:
        db_table = "zones"


class Department(models.Model):
    class Orientation(models.TextChoices):
        ENTRY = "ENTRY"
        COUNTER = "COUNTER"
        LEFT_TO_RIGHT = "LEFT_TO_RIGHT"

    name = models.CharField(max_length=255)
    orientation = models.CharField(max_length=20, choices=Orientation.choices)
    zone = models.ForeignKey(Zone, related_name="departments", on_delete=models.PROTECT)

    class Meta:
        db_table = "departments"


class Level(models.Model):
    name = models.CharField(max_length=255)
    label = models.CharField(max_length=255, null=True, blank=True)
    hex_color = models.CharField(max_length=255)
    divisions = ArrayField(models.CharField(max_length=255), default=list)
    department = models.ForeignKey(Department, related_name="levels", on_delete=models.PROTECT)

    class Meta:
        db_table = "levels"
