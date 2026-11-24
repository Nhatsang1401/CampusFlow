from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
)

User = get_user_model()


class CampusFlowLoginForm(AuthenticationForm):
    """Vietnamese login form."""

    username = forms.CharField(
        label="Tên đăng nhập",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập tên đăng nhập",
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
    )

    password = forms.CharField(
        label="Mật khẩu",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập mật khẩu",
                "autocomplete": "current-password",
            }
        ),
    )


class ProfileUpdateForm(forms.ModelForm):
    """Allow users to update their own profile."""

    email = forms.EmailField(
        label="Địa chỉ email",
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập địa chỉ email",
            }
        ),
    )

    class Meta:
        model = User

        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
        ]

        labels = {
            "first_name": "Tên",
            "last_name": "Họ và tên đệm",
            "phone_number": "Số điện thoại",
        }

        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nhập tên",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nhập họ và tên đệm",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ví dụ: 0912345678",
                    "inputmode": "tel",
                    "maxlength": "15",
                }
            ),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip()

        duplicated = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists()

        if duplicated:
            raise forms.ValidationError("Địa chỉ email này đã được sử dụng.")

        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number", "").strip()

        if phone and not phone.isdigit():
            raise forms.ValidationError("Số điện thoại chỉ được chứa chữ số.")

        if phone and not 9 <= len(phone) <= 15:
            raise forms.ValidationError("Số điện thoại phải có từ 9 đến 15 chữ số.")

        return phone


class CampusFlowPasswordChangeForm(PasswordChangeForm):
    """Vietnamese password change form."""

    old_password = forms.CharField(
        label="Mật khẩu hiện tại",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "current-password",
            }
        ),
    )

    new_password1 = forms.CharField(
        label="Mật khẩu mới",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
            }
        ),
    )

    new_password2 = forms.CharField(
        label="Xác nhận mật khẩu mới",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
            }
        ),
    )
