from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.models import UserRole


class Gender(models.TextChoices):
    MALE = "male", "Nam"
    FEMALE = "female", "Nữ"
    OTHER = "other", "Khác"


class Faculty(models.Model):
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Mã khoa",
    )
    name = models.CharField(
        max_length=150,
        verbose_name="Tên khoa",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Mô tả",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Đang hoạt động",
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    class Meta:
        db_table = "academics_faculty"
        verbose_name = "Khoa"
        verbose_name_plural = "Danh sách khoa"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class AcademicClass(models.Model):
    code = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Mã lớp",
    )
    name = models.CharField(
        max_length=150,
        verbose_name="Tên lớp",
    )
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.PROTECT,
        related_name="classes",
        verbose_name="Khoa",
    )
    academic_year = models.CharField(
        max_length=9,
        verbose_name="Niên khóa",
        help_text="Ví dụ: 2024-2028",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Đang hoạt động",
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    class Meta:
        db_table = "academics_class"
        verbose_name = "Lớp hành chính"
        verbose_name_plural = "Danh sách lớp hành chính"
        ordering = ["code"]
        indexes = [
            models.Index(
                fields=["faculty", "is_active"],
                name="acad_class_fac_active_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class StudentProfile(models.Model):
    student_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Mã sinh viên",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="student_profile",
        verbose_name="Tài khoản",
    )
    academic_class = models.ForeignKey(
        AcademicClass,
        on_delete=models.PROTECT,
        related_name="students",
        verbose_name="Lớp hành chính",
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name="Ngày sinh",
    )
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True,
        default="",
        verbose_name="Giới tính",
    )
    address = models.TextField(
        blank=True,
        default="",
        verbose_name="Địa chỉ",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    class Meta:
        db_table = "academics_student_profile"
        verbose_name = "Hồ sơ sinh viên"
        verbose_name_plural = "Danh sách sinh viên"
        ordering = ["student_code"]
        indexes = [
            models.Index(
                fields=["academic_class", "student_code"],
                name="acad_student_class_code_idx",
            ),
        ]

    def clean(self):
        super().clean()

        if self.user_id:
            if self.user.is_superuser or self.user.role != UserRole.STUDENT:
                raise ValidationError({"user": ("Tài khoản được chọn phải có vai trò sinh viên.")})

    def __str__(self) -> str:
        return f"{self.student_code} - {self.user}"


class LecturerProfile(models.Model):
    lecturer_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Mã giảng viên",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="lecturer_profile",
        verbose_name="Tài khoản",
    )
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.PROTECT,
        related_name="lecturers",
        verbose_name="Khoa",
    )
    academic_title = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Học hàm / học vị",
    )
    office_room = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Phòng làm việc",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    class Meta:
        db_table = "academics_lecturer_profile"
        verbose_name = "Hồ sơ giảng viên"
        verbose_name_plural = "Danh sách giảng viên"
        ordering = ["lecturer_code"]
        indexes = [
            models.Index(
                fields=["faculty", "lecturer_code"],
                name="acad_lect_fac_code_idx",
            ),
        ]

    def clean(self):
        super().clean()

        if self.user_id:
            if self.user.is_superuser or self.user.role != UserRole.LECTURER:
                raise ValidationError({"user": ("Tài khoản được chọn phải có vai trò giảng viên.")})

    def __str__(self) -> str:
        return f"{self.lecturer_code} - {self.user}"
