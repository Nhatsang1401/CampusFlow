import base64
import hashlib
import io
import secrets
from datetime import timedelta

import qrcode
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.academics.models import (
    ClassSession,
    ClassSessionStatus,
    Enrollment,
    EnrollmentStatus,
    StudentProfile,
)
from apps.accounts.models import UserRole
from apps.core.models import NotificationType
from apps.core.services import (
    create_audit_log,
    create_notification,
    create_notifications,
)

from .models import (
    AttendanceRecord,
    AttendanceSession,
    AttendanceSessionStatus,
)

DEFAULT_SESSION_MINUTES = 5
MAX_SESSION_MINUTES = 120


def generate_token() -> str:
    """Generate a cryptographically secure opaque token."""
    return secrets.token_urlsafe(32)


def generate_qr_base64(payload: str) -> str:
    """Return a PNG QR image encoded as a base64 data URI."""
    image = qrcode.make(payload)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def get_session_token(token: str):
    """Return an active attendance session for a valid raw token."""
    if not isinstance(token, str) or not token or len(token) > 256:
        return None

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    session = (
        AttendanceSession.objects.select_related(
            "class_session",
            "class_session__timetable",
            "class_session__timetable__course_section",
        )
        .filter(
            token_hash=token_hash,
            status=AttendanceSessionStatus.OPEN,
        )
        .first()
    )

    if not session or not session.is_active:
        return None

    return session


def _validate_actor(user):
    if not user or not user.is_authenticated or not user.is_active:
        raise ValidationError("Tài khoản không hợp lệ hoặc đã bị vô hiệu hóa.")

    if not user.is_superuser and user.role != UserRole.LECTURER:
        raise ValidationError("Chỉ giảng viên mới được mở phiên điểm danh.")


def _get_registered_student_users(course_section):
    return list(
        StudentProfile.objects.filter(
            enrollments__course_section=course_section,
            enrollments__status=EnrollmentStatus.REGISTERED,
            user__is_active=True,
        )
        .values_list("user", flat=True)
        .distinct()
    )


@transaction.atomic
def create_attendance_session(
    *,
    class_session_id: int,
    user,
    duration_minutes: int = DEFAULT_SESSION_MINUTES,
    request=None,
):
    _validate_actor(user)

    if (
        isinstance(duration_minutes, bool)
        or not isinstance(duration_minutes, int)
        or not 1 <= duration_minutes <= MAX_SESSION_MINUTES
    ):
        raise ValidationError(f"Thời lượng phải từ 1 đến {MAX_SESSION_MINUTES} phút.")

    class_session = (
        ClassSession.objects.select_for_update()
        .select_related(
            "timetable",
            "timetable__course_section",
            "timetable__course_section__course",
            "timetable__course_section__lecturer",
        )
        .filter(pk=class_session_id)
        .first()
    )

    if class_session is None:
        raise ValidationError("Không tìm thấy buổi học.")

    if class_session.status == ClassSessionStatus.CANCELLED:
        raise ValidationError("Buổi học đã bị hủy.")

    course_section = class_session.timetable.course_section
    lecturer = course_section.lecturer

    if not user.is_superuser and lecturer.user_id != user.pk:
        raise ValidationError("Bạn không phụ trách buổi học này.")

    now = timezone.now()
    token = generate_token()

    session, created = AttendanceSession.objects.get_or_create(
        class_session=class_session,
        defaults={
            "token_hash": AttendanceSession.hash_token(token),
            "starts_at": now,
            "expires_at": now + timedelta(minutes=duration_minutes),
            "status": AttendanceSessionStatus.OPEN,
            "created_by": user,
        },
    )

    if not created:
        if session.status == AttendanceSessionStatus.CLOSED:
            raise ValidationError("Phiên điểm danh đã được đóng.")

        if session.expires_at > now:
            raise ValidationError("Buổi học đã có phiên điểm danh chưa hết hạn.")

        # Rotate the token of an expired session.
        session.token_hash = AttendanceSession.hash_token(token)
        session.starts_at = now
        session.expires_at = now + timedelta(minutes=duration_minutes)
        session.status = AttendanceSessionStatus.OPEN
        session.created_by = user

    session.full_clean()
    session.save()

    action = "attendance.session.created" if created else "attendance.session.rotated"

    create_audit_log(
        actor=user,
        action=action,
        object_type="AttendanceSession",
        object_id=session.pk,
        description="Giảng viên mở phiên điểm danh.",
        changes={
            "class_session_id": class_session.pk,
            "course_section_id": course_section.pk,
            "duration_minutes": duration_minutes,
            "expires_at": session.expires_at.isoformat(),
        },
        request=request,
    )

    student_user_ids = _get_registered_student_users(course_section)
    from django.contrib.auth import get_user_model

    User = get_user_model()
    recipients = User.objects.filter(
        pk__in=student_user_ids,
        is_active=True,
    )

    create_notifications(
        recipients=recipients,
        title="Phiên điểm danh đã mở",
        message=(
            f"Giảng viên đã mở điểm danh cho học phần "
            f"{course_section.course.code} - {course_section.course.name}. "
            f"Vui lòng thực hiện điểm danh trong thời gian quy định."
        ),
        notification_type=NotificationType.INFO,
        link="/diem-danh/",
    )

    return session, token


@transaction.atomic
def close_attendance_session(*, session_id: int, user, request=None):
    _validate_actor(user)

    session = (
        AttendanceSession.objects.select_for_update()
        .select_related(
            "class_session__timetable__course_section__course",
            "class_session__timetable__course_section__lecturer",
        )
        .filter(pk=session_id)
        .first()
    )

    if session is None:
        raise ValidationError("Không tìm thấy phiên điểm danh.")

    course_section = session.class_session.timetable.course_section
    lecturer = course_section.lecturer

    if not user.is_superuser and lecturer.user_id != user.pk:
        raise ValidationError("Bạn không có quyền đóng phiên này.")

    if session.status == AttendanceSessionStatus.CLOSED:
        raise ValidationError("Phiên điểm danh đã được đóng.")

    session.status = AttendanceSessionStatus.CLOSED
    session.full_clean()
    session.save(update_fields=["status", "updated_at"])

    create_audit_log(
        actor=user,
        action="attendance.session.closed",
        object_type="AttendanceSession",
        object_id=session.pk,
        description="Giảng viên đóng phiên điểm danh.",
        changes={
            "class_session_id": session.class_session_id,
            "course_section_id": course_section.pk,
            "status": AttendanceSessionStatus.CLOSED,
        },
        request=request,
    )

    student_user_ids = _get_registered_student_users(course_section)
    from django.contrib.auth import get_user_model

    User = get_user_model()
    recipients = User.objects.filter(
        pk__in=student_user_ids,
        is_active=True,
    )

    create_notifications(
        recipients=recipients,
        title="Phiên điểm danh đã đóng",
        message=(
            f"Phiên điểm danh của học phần "
            f"{course_section.course.code} - {course_section.course.name} "
            f"đã được giảng viên đóng."
        ),
        notification_type=NotificationType.WARNING,
        link="/diem-danh/",
    )

    return session


@transaction.atomic
def check_in_student(*, token: str, user, request=None):
    """
    Check in the authenticated student using a raw attendance token.

    The student identity is always derived from the authenticated user.
    Database uniqueness is the final protection against duplicate check-ins.
    """
    if not user or not user.is_authenticated or not user.is_active:
        raise ValidationError("Tài khoản không hợp lệ hoặc đã bị vô hiệu hóa.")

    if user.is_superuser or user.role != UserRole.STUDENT:
        raise ValidationError("Chỉ sinh viên mới được phép điểm danh.")

    if not isinstance(token, str) or not token or len(token) > 256:
        raise ValidationError("Mã điểm danh không hợp lệ.")

    try:
        student = user.student_profile
    except StudentProfile.DoesNotExist as exc:
        raise ValidationError("Tài khoản chưa được liên kết với hồ sơ sinh viên.") from exc

    token_hash = AttendanceSession.hash_token(token)

    session = (
        AttendanceSession.objects.select_for_update()
        .select_related(
            "class_session",
            "class_session__timetable",
            "class_session__timetable__course_section",
            "class_session__timetable__course_section__course",
        )
        .filter(token_hash=token_hash)
        .first()
    )

    if session is None:
        raise ValidationError("Mã điểm danh không tồn tại hoặc không hợp lệ.")

    if session.status != AttendanceSessionStatus.OPEN:
        raise ValidationError("Phiên điểm danh đã đóng.")

    now = timezone.now()

    if now < session.starts_at:
        raise ValidationError("Phiên điểm danh chưa bắt đầu.")

    if now >= session.expires_at:
        raise ValidationError("Mã điểm danh đã hết hạn.")

    class_session = session.class_session

    if class_session.status == ClassSessionStatus.CANCELLED:
        raise ValidationError("Buổi học đã bị hủy, không thể điểm danh.")

    course_section = class_session.timetable.course_section

    is_enrolled = Enrollment.objects.filter(
        student=student,
        course_section=course_section,
        status=EnrollmentStatus.REGISTERED,
    ).exists()

    if not is_enrolled:
        raise ValidationError("Bạn không có đăng ký hợp lệ trong lớp học phần này.")

    try:
        with transaction.atomic():
            record = AttendanceRecord.objects.create(
                attendance_session=session,
                student=student,
                checked_in_at=now,
            )
    except IntegrityError as exc:
        raise ValidationError("Bạn đã điểm danh cho buổi học này rồi.") from exc

    create_notification(
        recipient=user,
        title="Điểm danh thành công",
        message=(
            f"Bạn đã điểm danh thành công học phần "
            f"{course_section.course.code} - {course_section.course.name}."
        ),
        notification_type=NotificationType.SUCCESS,
        link="/diem-danh/lich-su/",
    )

    create_audit_log(
        actor=user,
        action="attendance.check_in.created",
        object_type="AttendanceRecord",
        object_id=record.pk,
        description="Sinh viên điểm danh thành công.",
        changes={
            "attendance_session_id": session.pk,
            "class_session_id": class_session.pk,
            "student_profile_id": student.pk,
            "checked_in_at": record.checked_in_at.isoformat(),
        },
        request=request,
    )

    return record
