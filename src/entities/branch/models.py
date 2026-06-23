from django.db import models


class Branch(models.Model):

    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    uf = models.CharField(max_length=2)
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  

    class Meta:
        db_table = "branches"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
