import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import UserRole

User = get_user_model()


@pytest.fixture
def admin_panel_users(db):
    admin = User.objects.create_superuser(
        username="panel_admin",
        email="panel_admin@example.com",
        password="TestPassword123!",
    )

    student = User.objects.create_user(
        username="panel_student",
        password="TestPassword123!",
        role=UserRole.STUDENT,
    )

    lecturer = User.objects.create_user(
        username="panel_lecturer",
        password="TestPassword123!",
        role=UserRole.LECTURER,
    )

    return {
        "admin": admin,
        "student": student,
        "lecturer": lecturer,
    }


@pytest.mark.django_db
class TestAdminPanelAccess:
    def test_admin_can_open_panel(self, client, admin_panel_users):
        client.force_login(admin_panel_users["admin"])

        response = client.get(reverse("admin_panel:dashboard"))

        assert response.status_code == 200
        assert response.context["total_users"] == 3

    def test_student_cannot_open_panel(self, client, admin_panel_users):
        client.force_login(admin_panel_users["student"])

        response = client.get(reverse("admin_panel:dashboard"))

        assert response.status_code == 302
        assert reverse("accounts:login") in response.url

    def test_lecturer_cannot_open_panel(self, client, admin_panel_users):
        client.force_login(admin_panel_users["lecturer"])

        response = client.get(reverse("admin_panel:user_list"))

        assert response.status_code == 302
        assert reverse("accounts:login") in response.url

    def test_anonymous_user_is_redirected_to_login(self, client):
        response = client.get(reverse("admin_panel:dashboard"))

        assert response.status_code == 302
        assert reverse("accounts:login") in response.url


@pytest.mark.django_db
class TestAdminUserManagement:
    def test_admin_can_list_users(self, client, admin_panel_users):
        client.force_login(admin_panel_users["admin"])

        response = client.get(reverse("admin_panel:user_list"))

        assert response.status_code == 200
        assert response.context["page_obj"].paginator.count == 2

    def test_superuser_is_not_shown_in_user_list(self, client, admin_panel_users):
        client.force_login(admin_panel_users["admin"])

        response = client.get(reverse("admin_panel:user_list"))

        usernames = [user.username for user in response.context["page_obj"].object_list]

        assert "panel_admin" not in usernames

    def test_user_list_search(self, client, admin_panel_users):
        client.force_login(admin_panel_users["admin"])

        response = client.get(
            reverse("admin_panel:user_list"),
            {"q": "panel_student"},
        )

        assert response.status_code == 200
        assert response.context["page_obj"].paginator.count == 1

    def test_user_list_filter_by_role(self, client, admin_panel_users):
        client.force_login(admin_panel_users["admin"])

        response = client.get(
            reverse("admin_panel:user_list"),
            {"role": UserRole.LECTURER},
        )

        assert response.status_code == 200
        users = response.context["page_obj"].object_list

        assert len(users) == 1
        assert users[0].role == UserRole.LECTURER

    def test_admin_can_create_student_account(self, client, admin_panel_users):
        client.force_login(admin_panel_users["admin"])

        response = client.post(
            reverse("admin_panel:user_create"),
            {
                "username": "new_panel_student",
                "first_name": "An",
                "last_name": "Nguyen",
                "email": "new_student@example.com",
                "phone_number": "0901234567",
                "role": UserRole.STUDENT,
                "is_active": "on",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
        )

        assert response.status_code == 302

        user = User.objects.get(username="new_panel_student")

        assert user.check_password("StrongPassword123!")
        assert user.role == UserRole.STUDENT
        assert user.is_active is True
        assert user.is_superuser is False

    def test_create_user_rejects_password_mismatch(self, client, admin_panel_users):
        client.force_login(admin_panel_users["admin"])

        response = client.post(
            reverse("admin_panel:user_create"),
            {
                "username": "password_mismatch_user",
                "role": UserRole.STUDENT,
                "password": "StrongPassword123!",
                "password_confirm": "DifferentPassword123!",
            },
        )

        assert response.status_code == 200
        assert not User.objects.filter(username="password_mismatch_user").exists()

    def test_admin_can_update_regular_user(self, client, admin_panel_users):
        client.force_login(admin_panel_users["admin"])
        student = admin_panel_users["student"]

        response = client.post(
            reverse("admin_panel:user_update", args=[student.pk]),
            {
                "username": student.username,
                "first_name": "Updated",
                "last_name": "Student",
                "email": "updated@example.com",
                "phone_number": "0912345678",
                "role": UserRole.STUDENT,
                "is_active": "on",
            },
        )

        assert response.status_code == 302

        student.refresh_from_db()

        assert student.first_name == "Updated"
        assert student.email == "updated@example.com"

    def test_admin_can_deactivate_user(self, client, admin_panel_users):
        client.force_login(admin_panel_users["admin"])
        student = admin_panel_users["student"]

        response = client.post(
            reverse(
                "admin_panel:user_toggle_active",
                args=[student.pk],
            )
        )

        assert response.status_code == 302

        student.refresh_from_db()
        assert student.is_active is False

    def test_admin_can_reactivate_user(self, client, admin_panel_users):
        client.force_login(admin_panel_users["admin"])
        student = admin_panel_users["student"]

        student.is_active = False
        student.save(update_fields=["is_active"])

        response = client.post(
            reverse(
                "admin_panel:user_toggle_active",
                args=[student.pk],
            )
        )

        assert response.status_code == 302

        student.refresh_from_db()
        assert student.is_active is True

    def test_cannot_edit_superuser(self, client, admin_panel_users):
        client.force_login(admin_panel_users["admin"])

        response = client.get(
            reverse(
                "admin_panel:user_update",
                args=[admin_panel_users["admin"].pk],
            )
        )

        assert response.status_code == 404

    def test_cannot_toggle_superuser(self, client, admin_panel_users):
        client.force_login(admin_panel_users["admin"])

        response = client.post(
            reverse(
                "admin_panel:user_toggle_active",
                args=[admin_panel_users["admin"].pk],
            )
        )

        assert response.status_code == 404
        admin_panel_users["admin"].refresh_from_db()
        assert admin_panel_users["admin"].is_active is True

    def test_get_request_cannot_toggle_user_status(self, client, admin_panel_users):
        client.force_login(admin_panel_users["admin"])
        student = admin_panel_users["student"]

        response = client.get(
            reverse(
                "admin_panel:user_toggle_active",
                args=[student.pk],
            )
        )

        assert response.status_code == 405

        student.refresh_from_db()
        assert student.is_active is True
