from enum import unique
from django.db import models

class UserRoles(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    BACKOFFICE = "BACKOFFICE", "Backoffice"
    REGIONAL_SUPERVISOR = "REGIONAL_SUPERVISOR", "Supervisor Regional"
    BRANCH = "BRANCH", "Loja"
    LAYOUT = "LAYOUT", "layout"    

class User(models.Model):

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)

    role = models.CharField(
        max_length=50,
        choices=UserRoles.choices,
        null=False,
        blank=False,
    )

    is_active = models.BooleanField(default=True)

    itec_user = models.IntegerField(
        null=False,
        blank=False,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user"

    def __str__(self):
        return self.name

