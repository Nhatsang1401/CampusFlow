import base64
from datetime import date, time, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APIClient

from apps.academics.models import (
    AcademicTerm,
    Classroom,
    ClassSession,
    Course,
    CourseSection,
    Faculty,
    LecturerProfile,
    Weekday,
)
from apps.accounts.models import User, UserRole
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


@pytest.fixture
def attendance_data(db):
    faculty = Faculty.objects.create(
        code="CNTT",
        name="Công nghệ thông tin",
    )

    lecturer_user = User.objects.create_user(
        username="attendance_lecturer",
        password="test-password",
        role=UserRole.LECTURER,
    )

    lecturer = LecturerProfile.objects.create(
        lecturer_code="GV-ATT-01",
        user=lecturer_user,
        faculty=faculty,
    )

    other_lecturer_user = User.objects.create_user(
        username="other_lecturer",
        password="test-password",
        role=UserRole.LECTURER,
    )

    other_lecturer = LecturerProfile.objects.create(
        lecturer_code="GV-ATT-02",
        user=other_lecturer_user,
        faculty=faculty,
    )

    student_user = User.objects.create_user(
        username="attendance_student",
        password="test-password",
        role=UserRole.STUDENT,
    )

    course = Course.objects.create(
        code="ATT101",
        name="Kiểm thử điểm danh",
        credits=3,
    )

    term = AcademicTerm.objects.create(
        code="ATT-HK1-2026",
        name="Học kỳ 1",
        academic_year="2026-2027",
        semester="1",
        start_date=date(2026, 9, 1),
        end_date=date(2027, 1, 31),
    )

    section = CourseSection.objects.create(
        code="ATT101-01",
        course=course,
        term=term,
        lecturer=lecturer,
        section_number=1,
        max_students=40,
    )

    classroom = Classroom.objects.create(
        code="ATT-A101",
        name="Phòng kiểm thử",
        floor=1,
        capacity=50,
    )

    timetable = __import__(
        "apps.academics.models",
        fromlist=["Timetable"],
    ).Timetable.objects.create(
        course_section=section,
        classroom=classroom,
        weekday=Weekday.MONDAY,
        start_time=time(7, 0),
        end_time=time(9, 0),
        effective_start=date(2026, 9, 1),
        effective_end=date(2027, 1, 31),
    )

    class_session = ClassSession.objects.create(
        timetable=timetable,
        session_date=date(2026, 9, 7),
    )

    return {
        "faculty": faculty,
        "lecturer_user": lecturer_user,
        "lecturer": lecturer,
        "other_lecturer_user": other_lecturer_user,
        "other_lecturer": other_lecturer,
        "student_user": student_user,
        "course": course,
        "term": term,
        "section": section,
        "classroom": classroom,
        "timetable": timetable,
        "class_session": class_session,
    }


@pytest.mark.django_db
class TestAttendanceSessionServices:
    def test_generate_token_returns_unique_tokens(self):
        first = generate_token()
        second = generate_token()

        assert first != second
        assert len(first) >= 32

    def test_generate_qr_returns_png_data_uri(self):
        result = generate_qr_base64("test-token")

        prefix = "data:image/png;base64,"

        assert result.startswith(prefix)

        image_bytes = base64.b64decode(result.removeprefix(prefix))
        assert image_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    def test_create_attendance_session_success(self, attendance_data):
        user = attendance_data["lecturer_user"]

        session, token = create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=user,
            duration_minutes=5,
        )

        session.refresh_from_db()

        assert session.pk is not None
        assert session.status == AttendanceSessionStatus.OPEN
        assert session.token_hash == AttendanceSession.hash_token(token)
        assert session.token_hash != token
        assert session.created_by == user
        assert session.expires_at > session.starts_at

    def test_get_session_token_returns_active_session(self, attendance_data):
        session, token = create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=attendance_data["lecturer_user"],
        )

        result = get_session_token(token)

        assert result.pk == session.pk

    def test_invalid_token_returns_none(self):
        assert get_session_token("") is None
        assert get_session_token("x" * 257) is None
        assert get_session_token("invalid-token") is None
        assert get_session_token(None) is None

    def test_expired_token_returns_none(self, attendance_data):
        session, token = create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=attendance_data["lecturer_user"],
        )

        now = timezone.now()

        session.starts_at = now - timedelta(minutes=10)
        session.expires_at = now - timedelta(seconds=1)

        session.save(update_fields=["starts_at", "expires_at"])

        assert get_session_token(token) is None

    def test_expired_session_can_rotate_token(self, attendance_data):
        user = attendance_data["lecturer_user"]

        session, old_token = create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=user,
        )

        now = timezone.now()

        session.starts_at = now - timedelta(minutes=10)
        session.expires_at = now - timedelta(seconds=1)

        session.save(update_fields=["starts_at", "expires_at"])

        new_session, new_token = create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=user,
        )

        assert new_session.pk == session.pk
        assert new_token != old_token
        assert new_session.token_hash == AttendanceSession.hash_token(new_token)

    def test_duplicate_open_session_is_rejected(self, attendance_data):
        user = attendance_data["lecturer_user"]
        class_session_id = attendance_data["class_session"].pk

        create_attendance_session(
            class_session_id=class_session_id,
            user=user,
        )

        with pytest.raises(ValidationError):
            create_attendance_session(
                class_session_id=class_session_id,
                user=user,
            )

    def test_closed_session_cannot_be_reopened(self, attendance_data):
        user = attendance_data["lecturer_user"]

        session, _ = create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=user,
        )

        close_attendance_session(
            session_id=session.pk,
            user=user,
        )

        with pytest.raises(ValidationError):
            create_attendance_session(
                class_session_id=attendance_data["class_session"].pk,
                user=user,
            )

    def test_student_cannot_create_session(self, attendance_data):
        with pytest.raises(ValidationError):
            create_attendance_session(
                class_session_id=attendance_data["class_session"].pk,
                user=attendance_data["student_user"],
            )

    def test_other_lecturer_cannot_create_session(self, attendance_data):
        with pytest.raises(ValidationError):
            create_attendance_session(
                class_session_id=attendance_data["class_session"].pk,
                user=attendance_data["other_lecturer_user"],
            )

    @pytest.mark.parametrize("duration", [0, -1, 121, True, 1.5])
    def test_invalid_duration_is_rejected(self, attendance_data, duration):
        with pytest.raises(ValidationError):
            create_attendance_session(
                class_session_id=attendance_data["class_session"].pk,
                user=attendance_data["lecturer_user"],
                duration_minutes=duration,
            )

    def test_lecturer_can_close_own_session(self, attendance_data):
        user = attendance_data["lecturer_user"]

        session, _ = create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=user,
        )

        closed_session = close_attendance_session(
            session_id=session.pk,
            user=user,
        )

        assert closed_session.status == AttendanceSessionStatus.CLOSED
        assert closed_session.is_active is False

    def test_other_lecturer_cannot_close_session(self, attendance_data):
        session, _ = create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=attendance_data["lecturer_user"],
        )

        with pytest.raises(ValidationError):
            close_attendance_session(
                session_id=session.pk,
                user=attendance_data["other_lecturer_user"],
            )


@pytest.mark.django_db
class TestAttendanceSessionAPI:
    def setup_method(self):
        self.client = APIClient()

    def test_anonymous_user_cannot_access_list(self):
        response = self.client.get("/api/attendance/sessions/")

        assert response.status_code == 403

    def test_student_cannot_access_attendance_api(self, attendance_data):
        self.client.force_authenticate(user=attendance_data["student_user"])

        response = self.client.get("/api/attendance/sessions/")

        assert response.status_code == 403

    def test_lecturer_can_create_session(self, attendance_data):
        user = attendance_data["lecturer_user"]
        self.client.force_authenticate(user=user)

        response = self.client.post(
            "/api/attendance/sessions/",
            {
                "class_session_id": attendance_data["class_session"].pk,
                "duration_minutes": 5,
            },
            format="json",
        )

        assert response.status_code == 201
        assert "token" in response.data
        assert response.data["qr_code"].startswith("data:image/png;base64,")
        assert "token_hash" not in response.data["session"]

    def test_api_rejects_invalid_duration(self, attendance_data):
        self.client.force_authenticate(user=attendance_data["lecturer_user"])

        response = self.client.post(
            "/api/attendance/sessions/",
            {
                "class_session_id": attendance_data["class_session"].pk,
                "duration_minutes": 0,
            },
            format="json",
        )

        assert response.status_code == 400

    def test_lecturer_can_list_own_sessions(self, attendance_data):
        user = attendance_data["lecturer_user"]

        create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=user,
        )

        self.client.force_authenticate(user=user)

        response = self.client.get("/api/attendance/sessions/")

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1

    def test_lecturer_cannot_view_another_lecturers_session(self, attendance_data):
        session, _ = create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=attendance_data["lecturer_user"],
        )

        self.client.force_authenticate(user=attendance_data["other_lecturer_user"])

        response = self.client.get(f"/api/attendance/sessions/{session.pk}/")

        assert response.status_code == 404

    def test_lecturer_can_close_own_session(self, attendance_data):
        user = attendance_data["lecturer_user"]

        session, _ = create_attendance_session(
            class_session_id=attendance_data["class_session"].pk,
            user=user,
        )

        self.client.force_authenticate(user=user)

        response = self.client.post(f"/api/attendance/sessions/{session.pk}/close/")

        assert response.status_code == 200
        assert response.data["status"] == AttendanceSessionStatus.CLOSED
