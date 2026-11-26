from django.contrib import admin

from .models import AuditLog, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "recipient",
        "title",
        "notification_type",
        "is_read",
        "created_at",
    )
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = (
        "recipient__username",
        "recipient__email",
        "title",
        "message",
    )
    readonly_fields = ("created_at", "read_at")
    raw_id_fields = ("recipient",)
    list_select_related = ("recipient",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "actor_label",
        "action",
        "object_type",
        "object_id",
        "ip_address",
        "created_at",
    )
    list_filter = ("action", "object_type", "created_at")
    search_fields = (
        "actor_label",
        "actor__username",
        "description",
        "object_id",
    )
    readonly_fields = (
        "actor",
        "actor_label",
        "action",
        "object_type",
        "object_id",
        "description",
        "changes",
        "ip_address",
        "user_agent",
        "created_at",
    )
    list_select_related = ("actor",)
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
