from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username="sinhvien01",
            email="sinhvien01@example.com",
            password="CampusFlow@2026",
            first_name="Nguyen",
            last_name="Van A",
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
