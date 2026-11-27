import pytest
from django.contrib.auth import get_user_model

from apps.academics.models import (
    Enrollment,
    EnrollmentStatus,
    StudentProfile,
)
from apps.accounts.models import UserRole
from apps.attendance.models import AttendanceRecord
from apps.attendance.services import (
    check_in_student,
    close_attendance_session,
    create_attendance_session,
)
from apps.core.models import AuditLog, Notification

User = get_user_model()


@pytest.mark.django_db
class TestAttendanceNotificationIntegration:
    def create_additional_student(
        self,
        attendance_data,
        *,
        username,
        student_code,
        is_active=True,
        enrollment_status=EnrollmentStatus.REGISTERED,
    ):
        user = User.objects.create_user(
            username=username,
            password="TestPassword123!",
            role=UserRole.STUDENT,
            is_active=is_active,
        )

        profile = StudentProfile.objects.create(
            user=user,
            student_code=student_code,
            academic_class=attendance_data["academic_class"],
        )

        enrollment = Enrollment.objects.create(
            student=profile,
            course_section=attendance_data["section"],
            status=enrollment_status,
        )

        return user, profile, enrollment

    def test_open_session_notifies_only_active_registered_students(self, attendance_data):
        student_user = attendance_data["student_user"]

        active_user, _, _ = self.create_additional_student(
            attendance_data,
            username="active_registered",
            student_code="SV010",
        )

        inactive_user, _, _ = self.create_additional_student(
            attendance_data,
            username="inactive_registered",
            student_code="SV011",
            is_active=False,
        )

        unregistered_user, _, _ = self.create_additional_student(
            attendance_data,
            username="cancelled_enrollment",
            student_code="SV012",
            enrollment_status=EnrollmentStatus.CANCELLED,
        )

        session, token = create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=attendance_data["lecturer_user"],
        )

        notifications = Notification.objects.all()

        assert notifications.count() == 2
        assert set(notifications.values_list("recipient_id", flat=True)) == {
            student_user.pk,
            active_user.pk,
        }

        assert not notifications.filter(recipient=inactive_user).exists()

        assert not notifications.filter(recipient=unregistered_user).exists()

        assert token
        assert session.pk is not None

        audit = AuditLog.objects.get(
            action="attendance.session.created",
            object_id=str(session.pk),
        )
        assert audit.actor == attendance_data["lecturer_user"]
        assert audit.object_type == "AttendanceSession"

    def test_close_session_notifies_registered_students_and_logs_audit(self, attendance_data):
        student_user = attendance_data["student_user"]

        active_user, _, _ = self.create_additional_student(
            attendance_data,
            username="close_active_student",
            student_code="SV020",
        )

        inactive_user, _, _ = self.create_additional_student(
            attendance_data,
            username="close_inactive_student",
            student_code="SV021",
            is_active=False,
        )

        session, _ = create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=attendance_data["lecturer_user"],
        )

        Notification.objects.all().delete()
        audit_count_before = AuditLog.objects.count()

        closed_session = close_attendance_session(
            session_id=session.pk,
            user=attendance_data["lecturer_user"],
        )

        assert AuditLog.objects.count() == audit_count_before + 1

        closed_session.refresh_from_db()

        assert closed_session.status == "closed"

        notifications = Notification.objects.all()

        assert notifications.count() == 2
        assert set(notifications.values_list("recipient_id", flat=True)) == {
            student_user.pk,
            active_user.pk,
        }

        assert not notifications.filter(recipient=inactive_user).exists()

        assert notifications.filter(title="Phiên điểm danh đã đóng").count() == 2

        audit = AuditLog.objects.get(
            action="attendance.session.closed",
            object_id=str(session.pk),
        )

        assert audit.actor == attendance_data["lecturer_user"]
        assert audit.object_type == "AttendanceSession"

    def test_successful_check_in_creates_notification_and_audit(self, attendance_data):
        session, token = create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=attendance_data["lecturer_user"],
        )

        Notification.objects.all().delete()
        audit_count_before = AuditLog.objects.count()

        record = check_in_student(
            token=token,
            user=attendance_data["student_user"],
        )

        assert AuditLog.objects.count() == audit_count_before + 1

        assert record.pk is not None
        assert record.attendance_session == session
        assert record.student == attendance_data["student_profile"]

        notification = Notification.objects.get(
            recipient=attendance_data["student_user"],
            title="Điểm danh thành công",
        )

        assert notification.notification_type == "success"
        assert notification.is_read is False

        audit = AuditLog.objects.get(
            action="attendance.check_in.created",
            object_id=str(record.pk),
        )

        assert audit.actor == attendance_data["student_user"]
        assert audit.object_type == "AttendanceRecord"
        assert audit.changes["attendance_session_id"] == session.pk
        assert audit.changes["student_profile_id"] == attendance_data["student_profile"].pk

    def test_duplicate_check_in_does_not_create_extra_events(self, attendance_data):
        _, token = create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=attendance_data["lecturer_user"],
        )

        check_in_student(
            token=token,
            user=attendance_data["student_user"],
        )

        notification_count = Notification.objects.count()
        audit_count = AuditLog.objects.count()
        record_count = AttendanceRecord.objects.count()

        from django.core.exceptions import ValidationError

        with pytest.raises(ValidationError, match="đã điểm danh"):
            check_in_student(
                token=token,
                user=attendance_data["student_user"],
            )

        assert AttendanceRecord.objects.count() == record_count
        assert Notification.objects.count() == notification_count
        assert AuditLog.objects.count() == audit_count

    def test_invalid_check_in_does_not_create_notification_or_audit(self, attendance_data):
        from django.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            check_in_student(
                token="invalid-token",
                user=attendance_data["student_user"],
            )

        assert AttendanceRecord.objects.count() == 0
        assert Notification.objects.count() == 0
        assert AuditLog.objects.count() == 0

    def test_unauthorized_lecturer_cannot_create_audit_or_notification(self, attendance_data):
        from django.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            create_attendance_session(
                class_session_id=attendance_data["class_session"].pk,
                user=attendance_data["other_lecturer"],
            )

        assert Notification.objects.count() == 0
        assert AuditLog.objects.count() == 0
