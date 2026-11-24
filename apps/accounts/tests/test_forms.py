from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.forms import ProfileUpdateForm

User = get_user_model()


class ProfileUpdateFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="sinhvien01",
            email="student@example.com",
            password="CampusFlow@2026",
        )

    def test_valid_profile_update(self):
        form = ProfileUpdateForm(
            data={
                "first_name": "An",
                "last_name": "Nguyen Van",
                "email": "new@example.com",
                "phone_number": "0912345678",
            },
            instance=self.user,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username="sinhvien02",
            email="other@example.com",
            password="CampusFlow@2026",
        )

        form = ProfileUpdateForm(
            data={
                "first_name": "An",
                "last_name": "Nguyen Van",
                "email": "OTHER@example.com",
                "phone_number": "0912345678",
            },
            instance=self.user,
        )

        self.assertFalse(form.is_valid())

        self.assertIn(
            "email",
            form.errors,
        )

    def test_invalid_phone_is_rejected(self):
        form = ProfileUpdateForm(
            data={
                "first_name": "An",
                "last_name": "Nguyen Van",
                "email": "new@example.com",
                "phone_number": "09ABC123",
            },
            instance=self.user,
        )

        self.assertFalse(form.is_valid())

        self.assertIn(
            "phone_number",
            form.errors,
        )

    def test_phone_length_is_validated(self):
        form = ProfileUpdateForm(
            data={
                "first_name": "An",
                "last_name": "Nguyen Van",
                "email": "new@example.com",
                "phone_number": "123",
            },
            instance=self.user,
        )

        self.assertFalse(form.is_valid())

        self.assertIn(
            "phone_number",
            form.errors,
        )

    def test_empty_phone_is_allowed(self):
        form = ProfileUpdateForm(
            data={
                "first_name": "An",
                "last_name": "Nguyen Van",
                "email": "new@example.com",
                "phone_number": "",
            },
            instance=self.user,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )
