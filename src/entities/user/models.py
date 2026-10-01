from django.db import models


class UserRoles(models.TextChoices):
    
    ADMIN = "ADMIN", "Admin"
    BACKOFFICE = "BACKOFFICE", "Backoffice"
    REGIONAL_SUPERVISOR = "REGIONAL_SUPERVISOR", "Regional supervisor"
    BRANCH = "BRANCH", "Branch"
    LAYOUT = "LAYOUT", "Layout"


class User(models.Model):

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  

    role = models.CharField(
        max_length=32, choices=UserRoles.choices, null=True, blank=True
    )
    is_active = models.BooleanField(default=False)

    itec_user = models.IntegerField(null=True, blank=True, unique=True)

    branches = models.ManyToManyField(
        "branch.Branch",
        related_name="users",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # "user" é palavra reservada no PostgreSQL — plural, como branches/products
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.email


class ResetToken(models.Model):

    # Tokens JWT assinados com HS512 podem ultrapassar o limite de 255 caracteres.
    token = models.TextField()
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reset_tokens",
    )

    class Meta:
        db_table = "reset_tokens"
        ordering = ["-created_at"]

    def __str__(self):
        return f"ResetToken(user={self.user_id})"
