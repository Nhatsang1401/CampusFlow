from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import status

from apps.academics.models import (
    ClassSessionStatus,
    EnrollmentStatus,
    StudentProfile,
)
from apps.accounts.models import UserRole
from apps.attendance.models import (
    AttendanceRecord,
    AttendanceSessionStatus,
)
from apps.attendance.services import (
    check_in_student,
    create_attendance_session,
)


@pytest.mark.django_db
class TestStudentCheckInService:
    def create_session(self, attendance_data):
        return create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=attendance_data["lecturer_user"],
            duration_minutes=5,
        )

    def test_student_can_check_in_successfully(self, attendance_data):
        session, token = self.create_session(attendance_data)

        record = check_in_student(
            token=token,
            user=attendance_data["student_user"],
        )

        assert record.pk is not None
        assert record.student == attendance_data["student_profile"]
        assert record.attendance_session == session
        assert AttendanceRecord.objects.count() == 1

    def test_invalid_token_is_rejected(self, attendance_data):
        with pytest.raises(ValidationError):
            check_in_student(
                token="invalid-token",
                user=attendance_data["student_user"],
            )

    def test_expired_session_is_rejected(self, attendance_data):
        session, token = self.create_session(attendance_data)

        session.starts_at = timezone.now() - timedelta(minutes=10)
        session.expires_at = timezone.now() - timedelta(seconds=1)
        session.save(update_fields=["starts_at", "expires_at"])

        with pytest.raises(ValidationError, match="hết hạn"):
            check_in_student(
                token=token,
                user=attendance_data["student_user"],
            )

    def test_closed_session_is_rejected(self, attendance_data):
        session, token = self.create_session(attendance_data)
        session.status = AttendanceSessionStatus.CLOSED
        session.save(update_fields=["status"])

        with pytest.raises(ValidationError, match="đã đóng"):
            check_in_student(
                token=token,
                user=attendance_data["student_user"],
            )

    def test_student_cannot_check_in_twice(self, attendance_data):
        _, token = self.create_session(attendance_data)

        check_in_student(
            token=token,
            user=attendance_data["student_user"],
        )

        with pytest.raises(ValidationError, match="đã điểm danh"):
            check_in_student(
                token=token,
                user=attendance_data["student_user"],
            )

        assert AttendanceRecord.objects.count() == 1

    def test_unenrolled_student_cannot_check_in(self, attendance_data):
        user_model = type(attendance_data["student_user"])

        another_user = user_model.objects.create_user(
            username="student_unenrolled",
            password="TestPassword123!",
            role=UserRole.STUDENT,
        )

        another_student = StudentProfile.objects.create(
            student_code="SV002",
            user=another_user,
            academic_class=attendance_data["academic_class"],
        )

        session, token = self.create_session(attendance_data)

        with pytest.raises(ValidationError, match="đăng ký hợp lệ"):
            check_in_student(
                token=token,
                user=another_user,
            )

        assert not AttendanceRecord.objects.filter(
            attendance_session=session,
            student=another_student,
        ).exists()

    def test_cancelled_enrollment_cannot_check_in(self, attendance_data):
        attendance_data["enrollment"].status = EnrollmentStatus.CANCELLED
        attendance_data["enrollment"].save(update_fields=["status"])

        _, token = self.create_session(attendance_data)

        with pytest.raises(ValidationError, match="đăng ký hợp lệ"):
            check_in_student(
                token=token,
                user=attendance_data["student_user"],
            )

    def test_cancelled_class_session_cannot_check_in(self, attendance_data):
        # Create the attendance session while the class session is valid.
        _, token = self.create_session(attendance_data)

        # Cancel the class session after the attendance session exists.
        attendance_data["class_session"].status = ClassSessionStatus.CANCELLED
        attendance_data["class_session"].save(update_fields=["status"])

        with pytest.raises(ValidationError, match="đã bị hủy"):
            check_in_student(
                token=token,
                user=attendance_data["student_user"],
            )

    def test_lecturer_cannot_check_in_as_student(self, attendance_data):
        _, token = self.create_session(attendance_data)

        with pytest.raises(ValidationError, match="Chỉ sinh viên"):
            check_in_student(
                token=token,
                user=attendance_data["lecturer_user"],
            )

    def test_inactive_student_cannot_check_in(self, attendance_data):
        _, token = self.create_session(attendance_data)

        student_user = attendance_data["student_user"]
        student_user.is_active = False
        student_user.save(update_fields=["is_active"])

        with pytest.raises(ValidationError, match="vô hiệu hóa"):
            check_in_student(
                token=token,
                user=student_user,
            )

    def test_rotated_token_does_not_allow_duplicate_check_in(
        self,
        attendance_data,
    ):
        session, old_token = self.create_session(attendance_data)

        check_in_student(
            token=old_token,
            user=attendance_data["student_user"],
        )

        session.expires_at = timezone.now() - timedelta(seconds=1)
        session.starts_at = timezone.now() - timedelta(minutes=10)
        session.save(update_fields=["starts_at", "expires_at"])

        rotated_session, new_token = self.create_session(attendance_data)

        assert rotated_session.pk == session.pk

        with pytest.raises(ValidationError, match="đã điểm danh"):
            check_in_student(
                token=new_token,
                user=attendance_data["student_user"],
            )

        assert AttendanceRecord.objects.count() == 1

    def test_student_without_profile_cannot_check_in(self, attendance_data):
        from apps.academics.models import Enrollment
        from apps.accounts.models import User

        _, token = self.create_session(attendance_data)

        student_profile = attendance_data["student_profile"]
        student_user_id = attendance_data["student_user"].pk

        # Enrollment.student sử dụng PROTECT nên phải xóa Enrollment trước.
        Enrollment.objects.filter(student_id=student_profile.pk).delete()

        # Xóa StudentProfile.
        student_profile.delete()

        # Lấy User mới từ database để tránh cache quan hệ cũ.
        fresh_student_user = User.objects.get(pk=student_user_id)

        # Kiểm tra trực tiếp database: hồ sơ không còn tồn tại.
        assert not hasattr(fresh_student_user, "student_profile")

        # Service phải từ chối tài khoản không có StudentProfile.
        with pytest.raises(ValidationError, match="chưa được liên kết"):
            check_in_student(
                token=token,
                user=fresh_student_user,
            )

    def test_future_session_cannot_be_used_yet(self, attendance_data):
        session, token = self.create_session(attendance_data)

        session.starts_at = timezone.now() + timedelta(minutes=10)
        session.expires_at = timezone.now() + timedelta(minutes=15)
        session.save(update_fields=["starts_at", "expires_at"])

        with pytest.raises(ValidationError, match="chưa bắt đầu"):
            check_in_student(
                token=token,
                user=attendance_data["student_user"],
            )

    def test_database_rejects_duplicate_attendance_record(
        self,
        attendance_data,
    ):
        from django.db import IntegrityError, transaction

        session, _ = self.create_session(attendance_data)

        AttendanceRecord.objects.create(
            attendance_session=session,
            student=attendance_data["student_profile"],
        )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                AttendanceRecord.objects.create(
                    attendance_session=session,
                    student=attendance_data["student_profile"],
                )


@pytest.mark.django_db
class TestStudentCheckInAPI:
    def test_student_can_check_in(self, api_client, attendance_data):
        _, token = create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=attendance_data["lecturer_user"],
        )

        api_client.force_authenticate(user=attendance_data["student_user"])

        response = api_client.post(
            "/api/attendance/check-in/",
            {"token": token},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["message"] == "Điểm danh thành công."
        assert response.data["record"]["student_code"] == "SV001"

    def test_student_can_view_own_records(self, api_client, attendance_data):
        _, token = create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=attendance_data["lecturer_user"],
        )

        check_in_student(
            token=token,
            user=attendance_data["student_user"],
        )

        api_client.force_authenticate(user=attendance_data["student_user"])

        response = api_client.get("/api/attendance/my-records/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_student_cannot_view_another_student_records(
        self,
        api_client,
        attendance_data,
    ):
        _, token = create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=attendance_data["lecturer_user"],
        )

        check_in_student(
            token=token,
            user=attendance_data["student_user"],
        )

        another_user = type(attendance_data["student_user"]).objects.create_user(
            username="student_other",
            password="TestPassword123!",
            role=UserRole.STUDENT,
        )

        StudentProfile.objects.create(
            student_code="SV003",
            user=another_user,
            academic_class=attendance_data["academic_class"],
        )

        api_client.force_authenticate(user=another_user)

        response = api_client.get("/api/attendance/my-records/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_lecturer_cannot_use_student_check_in_api(
        self,
        api_client,
        attendance_data,
    ):
        api_client.force_authenticate(user=attendance_data["lecturer_user"])

        response = api_client.post(
            "/api/attendance/check-in/",
            {"token": "some-token"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_anonymous_user_cannot_check_in(self, api_client):
        response = api_client.post(
            "/api/attendance/check-in/",
            {"token": "some-token"},
            format="json",
        )

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_missing_token_returns_400(self, api_client, attendance_data):
        api_client.force_authenticate(user=attendance_data["student_user"])

        response = api_client.post(
            "/api/attendance/check-in/",
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
