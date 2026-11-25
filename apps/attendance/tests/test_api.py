import pytest
from rest_framework import status

from apps.attendance.models import AttendanceSession


@pytest.mark.django_db
class TestAttendanceSessionAPI:
    def test_anonymous_user_cannot_list_sessions(self, api_client):
        response = api_client.get("/api/attendance/sessions/")

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_student_cannot_create_session(
        self,
        api_client,
        attendance_data,
    ):
        api_client.force_authenticate(user=attendance_data["student_user"])

        response = api_client.post(
            "/api/attendance/sessions/",
            {
                "class_session_id": attendance_data["class_session"].id,
                "duration_minutes": 5,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_lecturer_can_create_session(
        self,
        api_client,
        attendance_data,
    ):
        api_client.force_authenticate(user=attendance_data["lecturer_user"])

        response = api_client.post(
            "/api/attendance/sessions/",
            {
                "class_session_id": attendance_data["class_session"].id,
                "duration_minutes": 5,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert "token" in response.data
        assert "qr_code" in response.data
        assert AttendanceSession.objects.filter(
            class_session=attendance_data["class_session"]
        ).exists()

    def test_invalid_duration_returns_400(
        self,
        api_client,
        attendance_data,
    ):
        api_client.force_authenticate(user=attendance_data["lecturer_user"])

        response = api_client.post(
            "/api/attendance/sessions/",
            {
                "class_session_id": attendance_data["class_session"].id,
                "duration_minutes": 121,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_lecturer_can_list_own_sessions(
        self,
        api_client,
        attendance_data,
    ):
        api_client.force_authenticate(user=attendance_data["lecturer_user"])

        api_client.post(
            "/api/attendance/sessions/",
            {
                "class_session_id": attendance_data["class_session"].id,
                "duration_minutes": 5,
            },
            format="json",
        )

        response = api_client.get("/api/attendance/sessions/")

        assert response.status_code == status.HTTP_200_OK

    def test_lecturer_cannot_view_other_lecturer_session(
        self,
        api_client,
        attendance_data,
    ):
        api_client.force_authenticate(user=attendance_data["lecturer_user"])

        create_response = api_client.post(
            "/api/attendance/sessions/",
            {
                "class_session_id": attendance_data["class_session"].id,
                "duration_minutes": 5,
            },
            format="json",
        )

        session_id = create_response.data["session"]["id"]

        api_client.force_authenticate(user=attendance_data["other_lecturer"])

        response = api_client.get(f"/api/attendance/sessions/{session_id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_lecturer_can_close_own_session(
        self,
        api_client,
        attendance_data,
    ):
        api_client.force_authenticate(user=attendance_data["lecturer_user"])

        create_response = api_client.post(
            "/api/attendance/sessions/",
            {
                "class_session_id": attendance_data["class_session"].id,
                "duration_minutes": 5,
            },
            format="json",
        )

        session_id = create_response.data["session"]["id"]

        response = api_client.post(f"/api/attendance/sessions/{session_id}/close/")

        assert response.status_code == status.HTTP_200_OK
