from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import (
    CampusFlowLoginForm,
    CampusFlowPasswordChangeForm,
    ProfileUpdateForm,
)


class CampusFlowLoginView(LoginView):
    """Handle user authentication."""

    template_name = "accounts/login.html"
    authentication_form = CampusFlowLoginForm
    redirect_authenticated_user = True


class CampusFlowLogoutView(LogoutView):
    """Handle secure POST-based logout."""

    next_page = reverse_lazy("accounts:login")


@login_required
def profile_view(request):
    """Display the current user's profile."""

    return render(
        request,
        "accounts/profile.html",
        {
            "profile_user": request.user,
        },
    )


@login_required
def profile_update_view(request):
    """Update the current user's profile."""

    if request.method == "POST":
        form = ProfileUpdateForm(
            request.POST,
            instance=request.user,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Cập nhật thông tin cá nhân thành công.",
            )

            return redirect("accounts:profile")

        messages.error(
            request,
            "Vui lòng kiểm tra lại thông tin đã nhập.",
        )

    else:
        form = ProfileUpdateForm(
            instance=request.user,
        )

    return render(
        request,
        "accounts/profile_edit.html",
        {
            "form": form,
        },
    )


class CampusFlowPasswordChangeView(PasswordChangeView):
    """Handle password changes without logging out the user."""

    template_name = "accounts/password_change.html"
    form_class = CampusFlowPasswordChangeForm
    success_url = reverse_lazy("accounts:password_change_done")

    def form_valid(self, form):
        response = super().form_valid(form)

        update_session_auth_hash(
            self.request,
            self.request.user,
        )

        messages.success(
            self.request,
            "Đổi mật khẩu thành công.",
        )

        return response


class CampusFlowPasswordChangeDoneView(PasswordChangeDoneView):
    """Display successful password change."""

    template_name = "accounts/password_change_done.html"
