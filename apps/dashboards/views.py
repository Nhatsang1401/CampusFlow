
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from apps.accounts.models import UserRole

from .services import (
    get_admin_dashboard_data,
    get_lecturer_dashboard_data,
    get_student_dashboard_data,
)


def administrator_required(user):
    return (
        user.is_authenticated
        and user.is_active
        and user.is_superuser
    )


def lecturer_required(user):
    return (
        user.is_authenticated
        and user.is_active
        and not user.is_superuser
        and user.role == UserRole.LECTURER
    )


def student_required(user):
    return (
        user.is_authenticated
        and user.is_active
        and not user.is_superuser
        and user.role == UserRole.STUDENT
    )


@login_required
@require_GET
def dashboard_index(request):
    user = request.user

    if user.is_superuser:
        return redirect("dashboards:admin")

    if user.role == UserRole.LECTURER:
        return redirect("dashboards:lecturer")

    if user.role == UserRole.STUDENT:
        return redirect("dashboards:student")

    return redirect("accounts:profile")


@login_required
@user_passes_test(administrator_required)
@require_GET
def admin_dashboard(request):
    context = get_admin_dashboard_data()

    return render(
        request,
        "dashboards/admin_dashboard.html",
        context,
    )


@login_required
@user_passes_test(lecturer_required)
@require_GET
def lecturer_dashboard(request):
    context = get_lecturer_dashboard_data(request.user)

    return render(
        request,
        "dashboards/lecturer_dashboard.html",
        context,
    )


@login_required
@user_passes_test(student_required)
@require_GET
def student_dashboard(request):
    context = get_student_dashboard_data(request.user)

    return render(
        request,
        "dashboards/student_dashboard.html",
        context,
    )
