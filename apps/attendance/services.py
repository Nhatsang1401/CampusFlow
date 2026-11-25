import base64
import hashlib
import io
import secrets
from datetime import timedelta

import qrcode
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.academics.models import ClassSession, ClassSessionStatus
from apps.accounts.models import UserRole

from .models import AttendanceSession, AttendanceSessionStatus

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


@transaction.atomic
def create_attendance_session(
    *,
    class_session_id: int,
    user,
    duration_minutes: int = DEFAULT_SESSION_MINUTES,
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
            "timetable__course_section__lecturer",
        )
        .filter(pk=class_session_id)
        .first()
    )

    if class_session is None:
        raise ValidationError("Không tìm thấy buổi học.")

    if class_session.status == ClassSessionStatus.CANCELLED:
        raise ValidationError("Buổi học đã bị hủy.")

    lecturer = class_session.timetable.course_section.lecturer

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

    return session, token


@transaction.atomic
def close_attendance_session(*, session_id: int, user):
    _validate_actor(user)

    session = (
        AttendanceSession.objects.select_for_update()
        .select_related(
            "class_session__timetable__course_section__lecturer",
        )
        .filter(pk=session_id)
        .first()
    )

    if session is None:
        raise ValidationError("Không tìm thấy phiên điểm danh.")

    lecturer = session.class_session.timetable.course_section.lecturer

    if not user.is_superuser and lecturer.user_id != user.pk:
        raise ValidationError("Bạn không có quyền đóng phiên này.")

    if session.status == AttendanceSessionStatus.CLOSED:
        raise ValidationError("Phiên điểm danh đã được đóng.")

    session.status = AttendanceSessionStatus.CLOSED
    session.full_clean()
    session.save(update_fields=["status", "updated_at"])

    return session
