from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "last_name", "first_name", "middle_name", "role", "email", "is_active")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "last_name", "first_name", "email")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Электронный журнал", {"fields": ("role", "middle_name", "phone")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Электронный журнал", {"fields": ("role", "last_name", "first_name", "middle_name")}),
    )
