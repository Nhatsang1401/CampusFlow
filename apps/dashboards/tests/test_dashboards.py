
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import UserRole

User = get_user_model()


@pytest.fixture
def dashboard_users(db):
    admin = User.objects.create_superuser(
        username="dashboard_admin",
        email="dashboard_admin@example.com",
        password="TestPassword123!",
    )

    lecturer = User.objects.create_user(
        username="dashboard_lecturer",
        password="TestPassword123!",
        role=UserRole.LECTURER,
    )

    student = User.objects.create_user(
        username="dashboard_student",
        password="TestPassword123!",
        role=UserRole.STUDENT,
    )

    return {
        "admin": admin,
        "lecturer": lecturer,
        "student": student,
    }


@pytest.mark.django_db
class TestDashboardRouting:
    def test_admin_is_redirected_to_admin_dashboard(
        self, client, dashboard_users
    ):
        client.force_login(dashboard_users["admin"])

        response = client.get(reverse("dashboards:index"))

        assert response.status_code == 302
        assert response.url == reverse("dashboards:admin")

    def test_lecturer_is_redirected_to_lecturer_dashboard(
        self, client, dashboard_users
    ):
        client.force_login(dashboard_users["lecturer"])

        response = client.get(reverse("dashboards:index"))

        assert response.status_code == 302
        assert response.url == reverse("dashboards:lecturer")

    def test_student_is_redirected_to_student_dashboard(
        self, client, dashboard_users
    ):
        client.force_login(dashboard_users["student"])

        response = client.get(reverse("dashboards:index"))

        assert response.status_code == 302
        assert response.url == reverse("dashboards:student")

    def test_anonymous_user_is_redirected_to_login(self, client):
        response = client.get(reverse("dashboards:index"))

        assert response.status_code == 302
        assert reverse("accounts:login") in response.url


@pytest.mark.django_db
class TestRoleBasedDashboards:
    def test_admin_can_access_admin_dashboard(
        self, client, dashboard_users
    ):
        client.force_login(dashboard_users["admin"])

        response = client.get(reverse("dashboards:admin"))

        assert response.status_code == 200
        assert response.context["total_users"] == 3
        assert response.context["total_students"] == 0
        assert response.context["total_lecturers"] == 0

    def test_lecturer_can_access_lecturer_dashboard_without_profile(
        self, client, dashboard_users
    ):
        client.force_login(dashboard_users["lecturer"])

        response = client.get(reverse("dashboards:lecturer"))

        assert response.status_code == 200
        assert response.context["has_profile"] is False
        assert response.context["total_sections"] == 0

    def test_student_can_access_student_dashboard_without_profile(
        self, client, dashboard_users
    ):
        client.force_login(dashboard_users["student"])

        response = client.get(reverse("dashboards:student"))

        assert response.status_code == 200
        assert response.context["has_profile"] is False
        assert response.context["total_sections"] == 0

    def test_student_cannot_access_admin_dashboard(
        self, client, dashboard_users
    ):
        client.force_login(dashboard_users["student"])

        response = client.get(reverse("dashboards:admin"))

        assert response.status_code == 302
        assert reverse("accounts:login") in response.url

    def test_lecturer_cannot_access_student_dashboard(
        self, client, dashboard_users
    ):
        client.force_login(dashboard_users["lecturer"])

        response = client.get(reverse("dashboards:student"))

        assert response.status_code == 302
        assert reverse("accounts:login") in response.url

    def test_admin_cannot_access_lecturer_dashboard(
        self, client, dashboard_users
    ):
        client.force_login(dashboard_users["admin"])

        response = client.get(reverse("dashboards:lecturer"))

        assert response.status_code == 302
        assert reverse("accounts:login") in response.url
