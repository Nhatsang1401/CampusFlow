from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "get_display_name",
        "email",
        "phone_number",
        "display_role",
        "is_active",
        "is_staff",
    )

    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "phone_number",
    )

    ordering = ("username",)

    readonly_fields = (
        "last_login",
        "date_joined",
    )

    fieldsets = (
        (
            "Thông tin đăng nhập",
            {
                "fields": (
                    "username",
                    "password",
                )
            },
        ),
        (
            "Thông tin cá nhân",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "phone_number",
                )
            },
        ),
        (
            "Phân quyền",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Thông tin hệ thống",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                )
            },
        ),
    )

    @admin.display(description="Họ và tên")
    def get_display_name(self, obj):
        return obj.get_full_name() or obj.username
