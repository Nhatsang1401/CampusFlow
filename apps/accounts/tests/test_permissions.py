from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from apps.accounts.models import UserRole
from apps.accounts.permissions import role_required

User = get_user_model()


class RolePermissionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.student = User.objects.create_user(
            username="sinhvien01",
            password="CampusFlow@2026",
            role=UserRole.STUDENT,
        )

        self.lecturer = User.objects.create_user(
            username="giangvien01",
            password="CampusFlow@2026",
            role=UserRole.LECTURER,
        )

        self.admin = User.objects.create_superuser(
            username="admin01",
            email="admin@example.com",
            password="CampusFlow@2026",
        )

    def get_response(self, user, allowed_roles):
        @role_required(*allowed_roles)
        def protected_view(request):
            return HttpResponse("Truy cập thành công")

        request = self.factory.get("/protected/")
        request.user = user

        return protected_view(request)

    def test_student_can_access_student_view(self):
        response = self.get_response(
            self.student,
            ["student"],
        )

        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_lecturer_view(self):
        with self.assertRaises(PermissionDenied):
            self.get_response(
                self.student,
                ["lecturer"],
            )

    def test_lecturer_can_access_lecturer_view(self):
        response = self.get_response(
            self.lecturer,
            ["lecturer"],
        )

        self.assertEqual(response.status_code, 200)

    def test_lecturer_cannot_access_student_only_view(self):
        with self.assertRaises(PermissionDenied):
            self.get_response(
                self.lecturer,
                ["student"],
            )

    def test_admin_can_access_admin_view(self):
        response = self.get_response(
            self.admin,
            ["admin"],
        )

        self.assertEqual(response.status_code, 200)

    def test_admin_cannot_use_other_role(self):
        with self.assertRaises(PermissionDenied):
            self.get_response(
                self.admin,
                ["lecturer"],
            )

    def test_invalid_role_is_rejected(self):
        with self.assertRaises(ValueError):
            role_required("invalid_role")

    def test_empty_roles_are_rejected(self):
        with self.assertRaises(ValueError):
            role_required()

    def test_anonymous_user_is_redirected(self):
        @role_required("student")
        def protected_view(request):
            return HttpResponse("OK")

        request = self.factory.get("/protected/")
        request.user = AnonymousUser()

        response = protected_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            "/tai-khoan/dang-nhap/",
            response.url,
        )
