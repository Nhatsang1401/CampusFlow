from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AuthenticationViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="sinhvien01",
            email="student@example.com",
            password="CampusFlow@2026",
            first_name="An",
            last_name="Nguyen Van",
        )

    def test_login_page_is_accessible(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertEqual(response.status_code, 200)

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "sinhvien01",
                "password": "CampusFlow@2026",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertRedirects(
            response,
            reverse("accounts:profile"),
        )

    def test_login_with_invalid_password(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "sinhvien01",
                "password": "WrongPassword",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "sinhvien01",
                "password": "CampusFlow@2026",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_authenticated_user_is_redirected_from_login(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:login"))

        self.assertRedirects(
            response,
            reverse("accounts:profile"),
        )

    def test_logout_requires_post(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:logout"))

        self.assertEqual(response.status_code, 405)

    def test_logout_post(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("accounts:logout"))

        self.assertRedirects(
            response,
            reverse("accounts:login"),
        )


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="sinhvien01",
            email="student@example.com",
            password="CampusFlow@2026",
            first_name="An",
            last_name="Nguyen Van",
        )

    def test_anonymous_user_cannot_view_profile(self):
        response = self.client.get(reverse("accounts:profile"))

        self.assertEqual(response.status_code, 302)

        self.assertIn(
            reverse("accounts:login"),
            response.url,
        )

    def test_authenticated_user_can_view_profile(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:profile"))

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Hồ sơ cá nhân",
        )

        self.assertContains(
            response,
            "Sinh viên",
        )

    def test_user_can_update_own_profile(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:profile_edit"),
            {
                "first_name": "Binh",
                "last_name": "Tran Van",
                "email": "updated@example.com",
                "phone_number": "0987654321",
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:profile"),
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.first_name,
            "Binh",
        )

        self.assertEqual(
            self.user.email,
            "updated@example.com",
        )

    def test_user_cannot_update_profile_with_duplicate_email(self):
        User.objects.create_user(
            username="sinhvien02",
            email="other@example.com",
            password="CampusFlow@2026",
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:profile_edit"),
            {
                "first_name": "An",
                "last_name": "Nguyen Van",
                "email": "other@example.com",
                "phone_number": "0912345678",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.email,
            "student@example.com",
        )


class PasswordChangeViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="sinhvien01",
            email="student@example.com",
            password="CampusFlow@2026",
        )

    def test_password_change_requires_login(self):
        response = self.client.get(reverse("accounts:password_change"))

        self.assertEqual(response.status_code, 302)

    def test_password_change_with_wrong_old_password(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "WrongPassword",
                "new_password1": "NewCampusSecure!2026",
                "new_password2": "NewCampusSecure!2026",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()

        self.assertTrue(self.user.check_password("CampusFlow@2026"))

    def test_password_change_success(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "CampusFlow@2026",
                "new_password1": "NewCampusSecure!2026",
                "new_password2": "NewCampusSecure!2026",
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:password_change_done"),
        )

        self.user.refresh_from_db()

        self.assertTrue(self.user.check_password("NewCampusSecure!2026"))

        self.assertFalse(self.user.check_password("CampusFlow@2026"))

        self.assertIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_password_confirmation_must_match(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "CampusFlow@2026",
                "new_password1": "NewCampusSecure!2026",
                "new_password2": "DifferentPassword!2026",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()

        self.assertTrue(self.user.check_password("CampusFlow@2026"))
