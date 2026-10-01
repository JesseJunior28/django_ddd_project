from django.db import models


class Industry(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "industries"


class Brand(models.Model):
    name = models.CharField(max_length=255)
    industry = models.ForeignKey(Industry, related_name="brands", on_delete=models.PROTECT)

    class Meta:
        db_table = "brands"
