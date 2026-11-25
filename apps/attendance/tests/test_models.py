from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.attendance.models import (
    AttendanceSession,
    AttendanceSessionStatus,
)


@pytest.mark.django_db
class TestAttendanceSessionModel:
    def test_create_valid_attendance_session(self, attendance_data):
        now = timezone.now()

        session = AttendanceSession.objects.create(
            class_session=attendance_data["class_session"],
            token_hash=AttendanceSession.hash_token("test-token"),
            starts_at=now,
            expires_at=now + timedelta(minutes=5),
            created_by=attendance_data["lecturer_user"],
        )

        assert session.pk is not None
        assert session.status == AttendanceSessionStatus.OPEN

    def test_expiration_must_be_after_start(self, attendance_data):
        now = timezone.now()

        session = AttendanceSession(
            class_session=attendance_data["class_session"],
            token_hash=AttendanceSession.hash_token("invalid-time"),
            starts_at=now,
            expires_at=now,
            created_by=attendance_data["lecturer_user"],
        )

        with pytest.raises(ValidationError):
            session.full_clean()

    def test_hash_token_returns_sha256_hash(self):
        token = "campusflow-test-token"

        hashed = AttendanceSession.hash_token(token)

        assert len(hashed) == 64
        assert hashed != token
        assert hashed == AttendanceSession.hash_token(token)

    def test_session_for_cancelled_class_is_invalid(self, attendance_data):
        class_session = attendance_data["class_session"]
        class_session.status = "cancelled"
        class_session.save(update_fields=["status"])

        now = timezone.now()

        session = AttendanceSession(
            class_session=class_session,
            token_hash=AttendanceSession.hash_token("cancelled-token"),
            starts_at=now,
            expires_at=now + timedelta(minutes=5),
            created_by=attendance_data["lecturer_user"],
        )

        with pytest.raises(ValidationError):
            session.full_clean()
