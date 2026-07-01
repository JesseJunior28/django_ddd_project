from django.contrib import admin
from .models import User, ResetToken


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "role", "is_active", "created_at")
    search_fields = ("name", "email")
    list_filter = ("role", "is_active")
    # password é dado sensível: nunca exposto em list_display nem em fields/forms
    exclude = ("password",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(ResetToken)
class ResetTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "expires_at", "used_at", "created_at")
    readonly_fields = ("created_at",)

    # Tokens não devem ser editados manualmente, só inspecionados
    def has_change_permission(self, request, obj=None):
        return False
