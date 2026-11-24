from django.contrib import admin

from .models import AcademicClass, Faculty, LecturerProfile, StudentProfile


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "class_count",
        "is_active",
        "updated_at",
    )
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    ordering = ("code",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Số lớp")
    def class_count(self, obj):
        return obj.classes.count()


@admin.register(AcademicClass)
class AcademicClassAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "faculty",
        "academic_year",
        "student_count",
        "is_active",
    )
    list_filter = ("faculty", "academic_year", "is_active")
    search_fields = (
        "code",
        "name",
        "faculty__code",
        "faculty__name",
    )
    raw_id_fields = ("faculty",)
    ordering = ("code",)
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("faculty",)

    @admin.display(description="Số sinh viên")
    def student_count(self, obj):
        return obj.students.count()


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "student_code",
        "get_full_name",
        "get_username",
        "academic_class",
        "get_email",
    )
    list_filter = (
        "academic_class",
        "academic_class__faculty",
        "gender",
    )
    search_fields = (
        "student_code",
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "academic_class__code",
    )
    raw_id_fields = ("user", "academic_class")
    ordering = ("student_code",)
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("user", "academic_class")

    @admin.display(description="Họ và tên")
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    @admin.display(description="Tên đăng nhập")
    def get_username(self, obj):
        return obj.user.username

    @admin.display(description="Email")
    def get_email(self, obj):
        return obj.user.email


@admin.register(LecturerProfile)
class LecturerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "lecturer_code",
        "get_full_name",
        "get_username",
        "faculty",
        "academic_title",
    )
    list_filter = ("faculty",)
    search_fields = (
        "lecturer_code",
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "faculty__code",
        "faculty__name",
    )
    raw_id_fields = ("user", "faculty")
    ordering = ("lecturer_code",)
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("user", "faculty")

    @admin.display(description="Họ và tên")
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    @admin.display(description="Tên đăng nhập")
    def get_username(self, obj):
        return obj.user.username
