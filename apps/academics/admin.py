from django.contrib import admin
from django.db.models import Count, Q

from .models import (
    AcademicClass,
    AcademicTerm,
    Classroom,
    ClassSession,
    Course,
    CourseSection,
    Enrollment,
    EnrollmentStatus,
    Faculty,
    LecturerProfile,
    StudentProfile,
    Timetable,
)


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


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "credits",
        "section_count",
        "is_active",
        "updated_at",
    )
    list_filter = ("credits", "is_active")
    search_fields = ("code", "name", "description")
    ordering = ("code",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Số lớp học phần")
    def section_count(self, obj):
        return obj.sections.count()


@admin.register(AcademicTerm)
class AcademicTermAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "academic_year",
        "semester",
        "start_date",
        "end_date",
        "is_active",
    )
    list_filter = ("academic_year", "semester", "is_active")
    search_fields = ("code", "name", "academic_year")
    ordering = ("-academic_year", "semester")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "start_date"


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "course",
        "term",
        "lecturer",
        "section_number",
        "max_students",
        "get_enrolled_count",
        "registration_open",
        "is_active",
    )
    list_filter = (
        "term",
        "course",
        "lecturer__faculty",
        "registration_open",
        "is_active",
    )
    search_fields = (
        "code",
        "course__code",
        "course__name",
        "lecturer__lecturer_code",
        "lecturer__user__username",
    )
    raw_id_fields = ("course", "term", "lecturer")
    ordering = ("term", "course", "section_number")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("course", "term", "lecturer")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            active_enrollment_count=Count(
                "enrollments",
                filter=Q(
                    enrollments__status=EnrollmentStatus.REGISTERED,
                ),
            )
        )

    @admin.display(description="Đã đăng ký", ordering="active_enrollment_count")
    def get_enrolled_count(self, obj):
        return obj.active_enrollment_count


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course_section",
        "get_course",
        "get_term",
        "status",
        "registered_at",
    )
    list_filter = (
        "status",
        "course_section__term",
        "course_section__course",
    )
    search_fields = (
        "student__student_code",
        "student__user__username",
        "student__user__first_name",
        "student__user__last_name",
        "course_section__code",
        "course_section__course__code",
        "course_section__course__name",
    )
    raw_id_fields = ("student", "course_section")
    readonly_fields = ("registered_at", "updated_at")
    list_select_related = (
        "student",
        "student__user",
        "course_section",
        "course_section__course",
        "course_section__term",
    )
    ordering = ("-registered_at",)

    @admin.display(description="Học phần")
    def get_course(self, obj):
        return obj.course_section.course

    @admin.display(description="Học kỳ")
    def get_term(self, obj):
        return obj.course_section.term


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "building",
        "floor",
        "capacity",
        "classroom_type",
        "is_active",
    )
    list_filter = ("building", "classroom_type", "is_active")
    search_fields = ("code", "name", "building")
    ordering = ("building", "floor", "code")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = (
        "course_section",
        "weekday",
        "start_time",
        "end_time",
        "classroom",
        "effective_start",
        "effective_end",
        "is_active",
    )
    list_filter = (
        "weekday",
        "classroom",
        "is_active",
        "course_section__term",
    )
    search_fields = (
        "course_section__code",
        "course_section__course__code",
        "course_section__course__name",
        "classroom__code",
        "classroom__name",
        "course_section__lecturer__lecturer_code",
    )
    raw_id_fields = ("course_section", "classroom")
    list_select_related = (
        "course_section",
        "course_section__course",
        "course_section__lecturer",
        "classroom",
    )
    ordering = ("weekday", "start_time")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "effective_start"


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = (
        "session_date",
        "get_course_section",
        "get_weekday",
        "get_time",
        "get_classroom",
        "status",
    )
    list_filter = (
        "status",
        "session_date",
        "timetable__course_section__term",
        "timetable__classroom",
    )
    search_fields = (
        "timetable__course_section__code",
        "timetable__course_section__course__name",
        "timetable__classroom__code",
        "topic",
    )
    raw_id_fields = ("timetable",)
    list_select_related = (
        "timetable",
        "timetable__course_section",
        "timetable__course_section__course",
        "timetable__classroom",
    )
    ordering = ("-session_date",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "session_date"

    @admin.display(description="Lớp học phần")
    def get_course_section(self, obj):
        return obj.timetable.course_section

    @admin.display(description="Thứ")
    def get_weekday(self, obj):
        return obj.timetable.get_weekday_display()

    @admin.display(description="Thời gian")
    def get_time(self, obj):
        return f"{obj.timetable.start_time:%H:%M} - {obj.timetable.end_time:%H:%M}"

    @admin.display(description="Phòng")
    def get_classroom(self, obj):
        return obj.timetable.classroom
