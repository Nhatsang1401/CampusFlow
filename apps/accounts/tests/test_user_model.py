from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import UserRole

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username="sinhvien01",
            email="sinhvien01@example.com",
            password="CampusFlow@2026",
            first_name="Van A",
            last_name="Nguyen",
        )

        self.assertEqual(
            user.username,
            "sinhvien01",
        )

        self.assertTrue(user.check_password("CampusFlow@2026"))

        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_password_is_not_stored_as_plain_text(self):
        raw_password = "CampusFlow@2026"

        user = User.objects.create_user(
            username="sinhvien02",
            password=raw_password,
        )

        self.assertNotEqual(
            user.password,
            raw_password,
        )

        self.assertTrue(user.check_password(raw_password))

    def test_default_role_is_student(self):
        user = User.objects.create_user(
            username="sinhvien03",
            password="CampusFlow@2026",
        )

        self.assertEqual(
            user.role,
            UserRole.STUDENT,
        )

        self.assertEqual(
            user.display_role,
            "Sinh viên",
        )

    def test_lecturer_role(self):
        user = User.objects.create_user(
            username="giangvien01",
            password="CampusFlow@2026",
            role=UserRole.LECTURER,
        )

        self.assertEqual(
            user.display_role,
            "Giảng viên",
        )

    def test_superuser_is_administrator(self):
        user = User.objects.create_superuser(
            username="quantri01",
            email="admin@example.com",
            password="CampusFlow@2026",
        )

        self.assertTrue(user.is_administrator)

        self.assertEqual(
            user.display_role,
            "Quản trị viên",
        )

    def test_string_representation(self):
        user = User.objects.create_user(
            username="sinhvien04",
            password="CampusFlow@2026",
            first_name="An",
            last_name="Nguyen Van",
        )

        self.assertEqual(
            str(user),
            "Nguyen Van An",
        )
