import base64
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.attendance.models import (
    AttendanceSession,
    AttendanceSessionStatus,
)
from apps.attendance.services import (
    close_attendance_session,
    create_attendance_session,
    generate_qr_base64,
    generate_token,
    get_session_token,
)


@pytest.mark.django_db
class TestAttendanceSessionServices:
    def test_generate_token(self):
        token_1 = generate_token()
        token_2 = generate_token()

        assert isinstance(token_1, str)
        assert len(token_1) > 20
        assert token_1 != token_2

    def test_generate_qr_base64(self):
        result = generate_qr_base64("campusflow-test")

        assert result.startswith("data:image/png;base64,")

        encoded = result.split(",", 1)[1]
        image_bytes = base64.b64decode(encoded)

        assert image_bytes.startswith(b"\x89PNG")

    def test_create_attendance_session(self, attendance_data):
        session, raw_token = create_attendance_session(
            class_session_id=attendance_data["class_session"].id,
            user=attendance_data["lecturer_user"],
            duration_minutes=5,
        )

        session.refresh_from_db()

        assert session.pk is not None
        assert session.status == AttendanceSessionStatus.OPEN
        assert raw_token
        assert session.token_hash != raw_token
        assert session.token_hash == AttendanceSession.hash_token(raw_token)

    def test_get_session_token(self, attendance_data):
        session, raw_token = create_attendance_session(
            class_session_id=attendance_data["class_session"].id,
            user=attendance_data["lecturer_user"],
            duration_minutes=5,
        )

        result = get_session_token(raw_token)

        assert result is not None
        assert result.pk == session.pk

    def test_invalid_token_returns_none(self):
        assert get_session_token("invalid-token") is None
        assert get_session_token(None) is None

    def test_expired_token_returns_none(self, attendance_data):
        session, raw_token = create_attendance_session(
            class_session_id=attendance_data["class_session"].id,
            user=attendance_data["lecturer_user"],
            duration_minutes=5,
        )

        now = timezone.now()
        session.starts_at = now - timedelta(minutes=10)
        session.expires_at = now - timedelta(seconds=1)
        session.save(update_fields=["starts_at", "expires_at"])

        assert get_session_token(raw_token) is None

    def test_expired_session_can_rotate_token(self, attendance_data):
        session, old_token = create_attendance_session(
            class_session_id=attendance_data["class_session"].id,
            user=attendance_data["lecturer_user"],
            duration_minutes=5,
        )

        now = timezone.now()
        session.starts_at = now - timedelta(minutes=10)
        session.expires_at = now - timedelta(seconds=1)
        session.save(update_fields=["starts_at", "expires_at"])

        new_session, new_token = create_attendance_session(
            class_session_id=attendance_data["class_session"].id,
            user=attendance_data["lecturer_user"],
            duration_minutes=5,
        )

        assert new_session.pk == session.pk
        assert new_token != old_token
        assert new_session.token_hash == AttendanceSession.hash_token(new_token)

    def test_duplicate_open_session_is_rejected(self, attendance_data):
        create_attendance_session(
            class_session_id=attendance_data["class_session"].id,
            user=attendance_data["lecturer_user"],
            duration_minutes=5,
        )

        with pytest.raises(ValidationError):
            create_attendance_session(
                class_session_id=attendance_data["class_session"].id,
                user=attendance_data["lecturer_user"],
                duration_minutes=5,
            )

    def test_closed_session_cannot_be_reopened(self, attendance_data):
        session, _ = create_attendance_session(
            class_session_id=attendance_data["class_session"].id,
            user=attendance_data["lecturer_user"],
            duration_minutes=5,
        )

        close_attendance_session(
            session_id=session.id,
            user=attendance_data["lecturer_user"],
        )

        with pytest.raises(ValidationError):
            create_attendance_session(
                class_session_id=attendance_data["class_session"].id,
                user=attendance_data["lecturer_user"],
                duration_minutes=5,
            )

    def test_student_cannot_create_session(self, attendance_data):
        with pytest.raises(ValidationError):
            create_attendance_session(
                class_session_id=attendance_data["class_session"].id,
                user=attendance_data["student_user"],
                duration_minutes=5,
            )

    def test_other_lecturer_cannot_create_session(self, attendance_data):
        with pytest.raises(ValidationError):
            create_attendance_session(
                class_session_id=attendance_data["class_session"].id,
                user=attendance_data["other_lecturer"],
                duration_minutes=5,
            )

    @pytest.mark.parametrize("duration", [0, -1, 121, True, 1.5])
    def test_invalid_duration(self, attendance_data, duration):
        with pytest.raises(ValidationError):
            create_attendance_session(
                class_session_id=attendance_data["class_session"].id,
                user=attendance_data["lecturer_user"],
                duration_minutes=duration,
            )

    def test_close_attendance_session(self, attendance_data):
        session, _ = create_attendance_session(
            class_session_id=attendance_data["class_session"].id,
            user=attendance_data["lecturer_user"],
            duration_minutes=5,
        )

        closed_session = close_attendance_session(
            session_id=session.id,
            user=attendance_data["lecturer_user"],
        )

        assert closed_session.status == AttendanceSessionStatus.CLOSED

    def test_other_lecturer_cannot_close_session(self, attendance_data):
        session, _ = create_attendance_session(
            class_session_id=attendance_data["class_session"].id,
            user=attendance_data["lecturer_user"],
            duration_minutes=5,
        )

        with pytest.raises(ValidationError):
            close_attendance_session(
                session_id=session.id,
                user=attendance_data["other_lecturer"],
            )
