from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    STUDENT = "student", "Sinh viên"
    LECTURER = "lecturer", "Giảng viên"


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
        verbose_name="Vai trò",
        db_index=True,
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        default="",
        verbose_name="Số điện thoại",
    )

    class Meta:
        db_table = "accounts_user"
        verbose_name = "Tài khoản"
        verbose_name_plural = "Danh sách tài khoản"
        ordering = ["username"]

    def __str__(self) -> str:
        full_name = f"{self.last_name} {self.first_name}".strip()
        return full_name or self.username

    @property
    def display_role(self) -> str:
        if self.is_superuser:
            return "Quản trị viên"
        return self.get_role_display()

    @property
    def is_administrator(self) -> bool:
        return self.is_superuser
