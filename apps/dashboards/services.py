from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone

from apps.academics.models import (
    AcademicClass,
    AcademicTerm,
    ClassSession,
    CourseSection,
    Enrollment,
    EnrollmentStatus,
    Faculty,
    LecturerProfile,
    StudentProfile,
)
from apps.attendance.models import AttendanceRecord
from apps.core.models import AuditLog, Notification

User = get_user_model()


def get_admin_dashboard_data():
    today = timezone.localdate()

    return {
        "total_users": User.objects.count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "total_students": StudentProfile.objects.count(),
        "total_lecturers": LecturerProfile.objects.count(),
        "total_faculties": Faculty.objects.count(),
        "total_classes": AcademicClass.objects.count(),
        "total_course_sections": CourseSection.objects.count(),
        "active_course_sections": CourseSection.objects.filter(is_active=True).count(),
        "total_terms": AcademicTerm.objects.count(),
        "total_class_sessions": ClassSession.objects.count(),
        "upcoming_sessions": ClassSession.objects.filter(
            session_date__gte=today,
            status="upcoming",
        ).count(),
        "completed_sessions": ClassSession.objects.filter(
            status="completed",
        ).count(),
        "total_attendance_records": AttendanceRecord.objects.count(),
        "total_audit_logs": AuditLog.objects.count(),
        "recent_audit_logs": AuditLog.objects.select_related("actor").order_by("-created_at")[:8],
    }


def get_lecturer_dashboard_data(user):
    today = timezone.localdate()

    try:
        profile = user.lecturer_profile
    except LecturerProfile.DoesNotExist:
        profile = None

    if profile is None:
        return {
            "has_profile": False,
            "total_sections": 0,
            "total_students": 0,
            "upcoming_sessions": [],
            "upcoming_session_count": 0,
            "total_attendance_records": 0,
        }

    sections = CourseSection.objects.filter(
        lecturer=profile,
        is_active=True,
    ).select_related("course", "term")

    section_ids = sections.values_list("pk", flat=True)

    total_students = (
        Enrollment.objects.filter(
            course_section_id__in=section_ids,
            status=EnrollmentStatus.REGISTERED,
        )
        .values("student_id")
        .distinct()
        .count()
    )

    sessions = list(
        ClassSession.objects.filter(
            timetable__course_section__lecturer=profile,
            timetable__course_section__is_active=True,
            session_date__gte=today,
            status="upcoming",
        )
        .select_related(
            "timetable__course_section__course",
            "timetable__classroom",
        )
        .order_by("session_date", "timetable__start_time")[:10]
    )

    session_ids = [session.pk for session in sessions]

    attendance_counts = dict(
        AttendanceRecord.objects.filter(
            attendance_session__class_session_id__in=session_ids,
        )
        .values("attendance_session__class_session_id")
        .annotate(total=Count("pk"))
        .values_list("attendance_session__class_session_id", "total")
    )

    enrollment_counts = dict(
        Enrollment.objects.filter(
            course_section_id__in=section_ids,
            status=EnrollmentStatus.REGISTERED,
        )
        .values("course_section_id")
        .annotate(total=Count("student_id", distinct=True))
        .values_list("course_section_id", "total")
    )

    for session in sessions:
        section = session.timetable.course_section
        session.registered_count = enrollment_counts.get(section.pk, 0)
        session.attendance_count = attendance_counts.get(session.pk, 0)

    total_attendance_records = AttendanceRecord.objects.filter(
        attendance_session__class_session__timetable__course_section__lecturer=profile,
    ).count()

    return {
        "has_profile": True,
        "lecturer_profile": profile,
        "sections": sections,
        "total_sections": sections.count(),
        "total_students": total_students,
        "upcoming_sessions": sessions,
        "upcoming_session_count": ClassSession.objects.filter(
            timetable__course_section__lecturer=profile,
            timetable__course_section__is_active=True,
            session_date__gte=today,
            status="upcoming",
        ).count(),
        "total_attendance_records": total_attendance_records,
    }


def get_student_dashboard_data(user):
    today = timezone.localdate()

    try:
        profile = user.student_profile
    except StudentProfile.DoesNotExist:
        profile = None

    if profile is None:
        return {
            "has_profile": False,
            "total_sections": 0,
            "upcoming_sessions": [],
            "recent_attendance": [],
            "unread_notifications": 0,
        }

    enrollments = Enrollment.objects.filter(
        student=profile,
        status=EnrollmentStatus.REGISTERED,
    ).select_related(
        "course_section__course",
        "course_section__term",
        "course_section__lecturer__user",
    )

    section_ids = enrollments.values_list("course_section_id", flat=True)

    sessions = list(
        ClassSession.objects.filter(
            timetable__course_section_id__in=section_ids,
            timetable__is_active=True,
            session_date__gte=today,
            status="upcoming",
        )
        .select_related(
            "timetable__course_section__course",
            "timetable__classroom",
            "timetable__course_section__lecturer__user",
        )
        .order_by("session_date", "timetable__start_time")[:10]
    )

    recent_attendance = (
        AttendanceRecord.objects.filter(student=profile)
        .select_related(
            "attendance_session__class_session__timetable__course_section__course",
        )
        .order_by("-checked_in_at")[:8]
    )

    return {
        "has_profile": True,
        "student_profile": profile,
        "enrollments": enrollments,
        "total_sections": enrollments.count(),
        "upcoming_sessions": sessions,
        "recent_attendance": recent_attendance,
        "unread_notifications": Notification.objects.filter(
            recipient=user,
            is_read=False,
        ).count(),
        "total_attendance_records": AttendanceRecord.objects.filter(
            student=profile,
        ).count(),
    }
