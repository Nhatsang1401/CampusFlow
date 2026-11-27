from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from apps.academics.models import (
    AcademicClass,
    AcademicTerm,
    Classroom,
    ClassroomType,
    ClassSession,
    ClassSessionStatus,
    Course,
    CourseSection,
    Enrollment,
    EnrollmentStatus,
    Faculty,
    LecturerProfile,
    StudentProfile,
    Timetable,
    Weekday,
)
from apps.attendance.models import AttendanceRecord, AttendanceSession
from apps.core.models import AuditLog, Notification

User = get_user_model()


def get_admin_panel_overview():
    return {
        "total_users": User.objects.count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "inactive_users": User.objects.filter(is_active=False).count(),
        "total_students": StudentProfile.objects.count(),
        "total_lecturers": LecturerProfile.objects.count(),
        "total_faculties": Faculty.objects.count(),
        "total_classes": AcademicClass.objects.count(),
        "total_terms": AcademicTerm.objects.count(),
        "total_course_sections": CourseSection.objects.count(),
        "total_enrollments": Enrollment.objects.count(),
        "total_class_sessions": ClassSession.objects.count(),
        "total_attendance_sessions": AttendanceSession.objects.count(),
        "total_attendance_records": AttendanceRecord.objects.count(),
        "total_notifications": Notification.objects.count(),
        "total_audit_logs": AuditLog.objects.count(),
        "recent_audit_logs": (AuditLog.objects.select_related("actor").order_by("-created_at")[:8]),
    }


def get_admin_user_queryset(*, query="", role="", active=""):
    queryset = User.objects.filter(is_superuser=False).order_by("username")
    if query:
        queryset = queryset.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone_number__icontains=query)
        )
    if role in ("student", "lecturer"):
        queryset = queryset.filter(role=role)
    if active == "active":
        queryset = queryset.filter(is_active=True)
    elif active == "inactive":
        queryset = queryset.filter(is_active=False)
    return queryset


def filter_queryset(queryset, query, fields):
    if query:
        condition = Q()
        for field in fields:
            condition |= Q(**{f"{field}__icontains": query})
        queryset = queryset.filter(condition)
    return queryset


def get_faculty_queryset(*, query="", active=""):
    queryset = Faculty.objects.all().order_by("code")
    queryset = filter_queryset(queryset, query, ("code", "name"))
    if active == "active":
        queryset = queryset.filter(is_active=True)
    elif active == "inactive":
        queryset = queryset.filter(is_active=False)
    return queryset


def get_academic_class_queryset(*, query="", faculty="", active=""):
    queryset = AcademicClass.objects.select_related("faculty").order_by("code")
    queryset = filter_queryset(queryset, query, ("code", "name", "faculty__code", "faculty__name"))
    if faculty.isdigit():
        queryset = queryset.filter(faculty_id=int(faculty))
    if active == "active":
        queryset = queryset.filter(is_active=True)
    elif active == "inactive":
        queryset = queryset.filter(is_active=False)
    return queryset


def get_student_profile_queryset(*, query="", faculty="", academic_class=""):
    queryset = StudentProfile.objects.select_related(
        "user", "academic_class", "academic_class__faculty"
    ).order_by("student_code")
    queryset = filter_queryset(
        queryset,
        query,
        (
            "student_code",
            "user__username",
            "user__first_name",
            "user__last_name",
            "user__email",
            "academic_class__code",
        ),
    )
    if faculty.isdigit():
        queryset = queryset.filter(academic_class__faculty_id=int(faculty))
    if academic_class.isdigit():
        queryset = queryset.filter(academic_class_id=int(academic_class))
    return queryset


def get_lecturer_profile_queryset(*, query="", faculty=""):
    queryset = LecturerProfile.objects.select_related("user", "faculty").order_by("lecturer_code")
    queryset = filter_queryset(
        queryset,
        query,
        (
            "lecturer_code",
            "user__username",
            "user__first_name",
            "user__last_name",
            "user__email",
            "faculty__code",
            "faculty__name",
        ),
    )
    if faculty.isdigit():
        queryset = queryset.filter(faculty_id=int(faculty))
    return queryset


def get_academic_term_queryset(*, query="", active=""):
    queryset = AcademicTerm.objects.all().order_by(
        "-academic_year",
        "semester",
    )

    if query:
        queryset = queryset.filter(
            Q(code__icontains=query) | Q(name__icontains=query) | Q(academic_year__icontains=query)
        )

    if active == "active":
        queryset = queryset.filter(is_active=True)
    elif active == "inactive":
        queryset = queryset.filter(is_active=False)

    return queryset


def get_course_queryset(*, query="", active=""):
    queryset = Course.objects.all().order_by("code")

    if query:
        queryset = queryset.filter(
            Q(code__icontains=query) | Q(name__icontains=query) | Q(description__icontains=query)
        )

    if active == "active":
        queryset = queryset.filter(is_active=True)
    elif active == "inactive":
        queryset = queryset.filter(is_active=False)

    return queryset


def get_course_section_queryset(
    *,
    query="",
    term="",
    course="",
    lecturer="",
    active="",
):
    queryset = CourseSection.objects.select_related(
        "course",
        "term",
        "lecturer",
        "lecturer__user",
        "lecturer__faculty",
    ).order_by("term__academic_year", "course__code", "section_number")

    if query:
        queryset = queryset.filter(
            Q(code__icontains=query)
            | Q(course__code__icontains=query)
            | Q(course__name__icontains=query)
            | Q(lecturer__lecturer_code__icontains=query)
            | Q(lecturer__user__first_name__icontains=query)
            | Q(lecturer__user__last_name__icontains=query)
        )

    if term:
        queryset = queryset.filter(term_id=term)

    if course:
        queryset = queryset.filter(course_id=course)

    if lecturer:
        queryset = queryset.filter(lecturer_id=lecturer)

    if active == "active":
        queryset = queryset.filter(is_active=True)
    elif active == "inactive":
        queryset = queryset.filter(is_active=False)

    return queryset


def get_enrollment_queryset(
    *,
    query="",
    section="",
    status="",
):
    queryset = Enrollment.objects.select_related(
        "student",
        "student__user",
        "student__academic_class",
        "course_section",
        "course_section__course",
        "course_section__term",
    ).order_by("-registered_at")

    if query:
        queryset = queryset.filter(
            Q(student__student_code__icontains=query)
            | Q(student__user__username__icontains=query)
            | Q(student__user__first_name__icontains=query)
            | Q(student__user__last_name__icontains=query)
            | Q(course_section__code__icontains=query)
            | Q(course_section__course__code__icontains=query)
            | Q(course_section__course__name__icontains=query)
        )

    if section:
        queryset = queryset.filter(course_section_id=section)

    if status in EnrollmentStatus.values:
        queryset = queryset.filter(status=status)

    return queryset


@transaction.atomic
def change_enrollment_status(*, enrollment_id, new_status):
    """
    Chuyển trạng thái đăng ký theo quy tắc nghiệp vụ.

    - registered -> cancelled
    - registered -> completed
    - cancelled -> registered (phải kiểm tra lại sức chứa)
    - completed là trạng thái kết thúc.
    """
    enrollment = (
        Enrollment.objects.select_for_update()
        .select_related("student", "student__user")
        .get(pk=enrollment_id)
    )

    section = CourseSection.objects.select_for_update().get(pk=enrollment.course_section_id)

    allowed_transitions = {
        EnrollmentStatus.REGISTERED: {
            EnrollmentStatus.CANCELLED,
            EnrollmentStatus.COMPLETED,
        },
        EnrollmentStatus.CANCELLED: {
            EnrollmentStatus.REGISTERED,
        },
        EnrollmentStatus.COMPLETED: set(),
    }

    if new_status not in EnrollmentStatus.values:
        raise ValidationError("Trạng thái đăng ký không hợp lệ.")

    if new_status == enrollment.status:
        return enrollment

    if new_status not in allowed_transitions[enrollment.status]:
        raise ValidationError("Không thể chuyển từ trạng thái hiện tại sang trạng thái được chọn.")

    if new_status == EnrollmentStatus.REGISTERED:
        if not enrollment.student.user.is_active:
            raise ValidationError("Không thể đăng ký cho tài khoản sinh viên đã bị khóa.")

        if not section.is_active:
            raise ValidationError("Không thể đăng ký vào lớp học phần đã ngừng hoạt động.")

        if not section.registration_open:
            raise ValidationError("Lớp học phần hiện không mở đăng ký.")

        registered_count = Enrollment.objects.filter(
            course_section=section,
            status=EnrollmentStatus.REGISTERED,
        ).count()

        if registered_count >= section.max_students:
            raise ValidationError("Lớp học phần đã đạt sĩ số tối đa.")

    enrollment.status = new_status
    enrollment.full_clean()
    enrollment.save(update_fields=["status", "updated_at"])

    return enrollment


def get_classroom_queryset(*, query="", building="", classroom_type="", active=""):
    queryset = Classroom.objects.all().order_by("building", "floor", "code")
    queryset = filter_queryset(
        queryset,
        query,
        ("code", "name", "building", "description"),
    )

    if building:
        queryset = queryset.filter(building__icontains=building)

    if classroom_type in ClassroomType.values:
        queryset = queryset.filter(classroom_type=classroom_type)

    if active == "active":
        queryset = queryset.filter(is_active=True)
    elif active == "inactive":
        queryset = queryset.filter(is_active=False)

    return queryset


def get_timetable_queryset(
    *,
    query="",
    term="",
    course_section="",
    classroom="",
    weekday="",
    active="",
):
    queryset = Timetable.objects.select_related(
        "course_section",
        "course_section__course",
        "course_section__term",
        "course_section__lecturer__user",
        "classroom",
    ).order_by("weekday", "start_time", "classroom__code")

    if query:
        queryset = queryset.filter(
            Q(course_section__code__icontains=query)
            | Q(course_section__course__code__icontains=query)
            | Q(course_section__course__name__icontains=query)
            | Q(classroom__code__icontains=query)
            | Q(classroom__name__icontains=query)
        )

    if term.isdigit():
        queryset = queryset.filter(course_section__term_id=int(term))

    if course_section.isdigit():
        queryset = queryset.filter(course_section_id=int(course_section))

    if classroom.isdigit():
        queryset = queryset.filter(classroom_id=int(classroom))

    if weekday.isdigit() and int(weekday) in Weekday.values:
        queryset = queryset.filter(weekday=int(weekday))

    if active == "active":
        queryset = queryset.filter(is_active=True)
    elif active == "inactive":
        queryset = queryset.filter(is_active=False)

    return queryset


def get_class_session_queryset(
    *,
    query="",
    term="",
    timetable="",
    classroom="",
    status="",
    date_from=None,
    date_to=None,
):
    queryset = ClassSession.objects.select_related(
        "timetable",
        "timetable__classroom",
        "timetable__course_section",
        "timetable__course_section__course",
        "timetable__course_section__term",
    ).order_by("-session_date", "timetable__start_time")

    if query:
        queryset = queryset.filter(
            Q(topic__icontains=query)
            | Q(timetable__course_section__code__icontains=query)
            | Q(timetable__course_section__course__name__icontains=query)
            | Q(timetable__classroom__code__icontains=query)
        )

    if term.isdigit():
        queryset = queryset.filter(timetable__course_section__term_id=int(term))

    if timetable.isdigit():
        queryset = queryset.filter(timetable_id=int(timetable))

    if classroom.isdigit():
        queryset = queryset.filter(timetable__classroom_id=int(classroom))

    if status in ClassSessionStatus.values:
        queryset = queryset.filter(status=status)

    if date_from:
        queryset = queryset.filter(session_date__gte=date_from)

    if date_to:
        queryset = queryset.filter(session_date__lte=date_to)

    return queryset


def get_audit_log_queryset(*, query="", action="", object_type=""):
    queryset = AuditLog.objects.select_related("actor").order_by("-created_at")

    if query:
        queryset = queryset.filter(
            Q(actor_label__icontains=query)
            | Q(description__icontains=query)
            | Q(object_id__icontains=query)
            | Q(action__icontains=query)
        )

    if action:
        queryset = queryset.filter(action=action)

    if object_type:
        queryset = queryset.filter(object_type=object_type)

    return queryset
