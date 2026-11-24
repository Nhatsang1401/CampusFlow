from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom user model for CampusFlow.

    Role and profile-specific fields will be introduced
    in Day 02 before the first production release.
    """

    class Meta:
        db_table = "accounts_user"
        verbose_name = "Tài khoản"
        verbose_name_plural = "Danh sách tài khoản"

    def __str__(self) -> str:
        return self.username
