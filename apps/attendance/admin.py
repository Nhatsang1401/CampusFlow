from django.contrib import admin

from .models import AttendanceSession


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "class_session",
        "starts_at",
        "expires_at",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "starts_at", "expires_at")
    search_fields = (
        "class_session__timetable__course_section__code",
        "class_session__timetable__course_section__course__name",
        "created_by__username",
    )
    readonly_fields = (
        "token_hash",
        "created_at",
        "updated_at",
    )
    raw_id_fields = ("class_session", "created_by")
    list_select_related = (
        "class_session",
        "created_by",
        "class_session__timetable",
    )
