from rest_framework.permissions import BasePermission

from apps.accounts.models import UserRole


class IsLecturerOrAdmin(BasePermission):
    message = "Chỉ giảng viên hoặc quản trị viên được phép thực hiện thao tác này."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and (user.is_superuser or user.role == UserRole.LECTURER)
        )


class IsStudent(BasePermission):
    message = "Chỉ sinh viên có tài khoản hoạt động mới được phép thực hiện thao tác này."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and not user.is_superuser
            and user.role == UserRole.STUDENT
        )
