from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import UserRole

VALID_ROLES = {
    "admin",
    *UserRole.values,
}


def role_required(*allowed_roles: str):
    """Restrict access to selected CampusFlow roles."""

    if not allowed_roles:
        raise ValueError("Phải khai báo ít nhất một vai trò.")

    invalid_roles = set(allowed_roles) - VALID_ROLES

    if invalid_roles:
        raise ValueError(f"Vai trò không hợp lệ: {sorted(invalid_roles)}")

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            user = request.user

            if "admin" in allowed_roles and user.is_superuser:
                return view_func(request, *args, **kwargs)

            if user.is_superuser:
                raise PermissionDenied("Quản trị viên không sử dụng quyền của tài khoản khác.")

            if user.role not in allowed_roles:
                raise PermissionDenied("Bạn không có quyền truy cập chức năng này.")

            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator
