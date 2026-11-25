from rest_framework.permissions import BasePermission

from apps.accounts.models import UserRole


class IsLecturerOrAdmin(BasePermission):
    message = "Chỉ giảng viên hoặc quản trị viên được phép thực hiện thao tác này."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and (user.is_superuser or user.role == UserRole.LECTURER)
        )
