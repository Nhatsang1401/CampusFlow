from rest_framework.permissions import BasePermission


class IsAdministrator(BasePermission):
    message = "Chỉ quản trị viên mới được phép xem nhật ký kiểm toán."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.is_superuser)
