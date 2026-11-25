import hashlib

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from apps.academics.models import ClassSessionStatus


class AttendanceSessionStatus(models.TextChoices):
    OPEN = "open", "Đang mở"
    CLOSED = "closed", "Đã đóng"


class AttendanceSession(models.Model):
    class_session = models.OneToOneField(
        "academics.ClassSession",
        on_delete=models.PROTECT,
        related_name="attendance_session",
        verbose_name="Buổi học",
    )
    token_hash = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        verbose_name="SHA-256 token",
    )
    starts_at = models.DateTimeField(verbose_name="Bắt đầu")
    expires_at = models.DateTimeField(verbose_name="Hết hạn")
    status = models.CharField(
        max_length=10,
        choices=AttendanceSessionStatus.choices,
        default=AttendanceSessionStatus.OPEN,
        db_index=True,
        verbose_name="Trạng thái",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_attendance_sessions",
        verbose_name="Người tạo",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "attendance_session"
        verbose_name = "Phiên điểm danh"
        verbose_name_plural = "Danh sách phiên điểm danh"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["status", "expires_at"],
                name="att_session_status_exp_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(expires_at__gt=F("starts_at")),
                name="att_session_exp_after_start",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}

        if self.starts_at and self.expires_at:
            if self.expires_at <= self.starts_at:
                errors["expires_at"] = "Thời điểm hết hạn phải sau thời điểm bắt đầu."

        if self.class_session_id:
            if self.class_session.status == ClassSessionStatus.CANCELLED:
                errors["class_session"] = "Không thể mở điểm danh cho buổi học đã bị hủy."

        if errors:
            raise ValidationError(errors)

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_active(self):
        now = timezone.now()
        return (
            self.status == AttendanceSessionStatus.OPEN and self.starts_at <= now < self.expires_at
        )

    @property
    def display_status(self):
        if self.status == AttendanceSessionStatus.CLOSED:
            return AttendanceSessionStatus.CLOSED.label

        now = timezone.now()

        if now < self.starts_at:
            return "Sắp diễn ra"

        if now >= self.expires_at:
            return "Đã hết hạn"

        return "Đang mở"

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def __str__(self):
        return f"Điểm danh - {self.class_session}"


class AttendanceRecord(models.Model):
    attendance_session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.PROTECT,
        related_name="attendance_records",
        verbose_name="Phiên điểm danh",
    )
    student = models.ForeignKey(
        "academics.StudentProfile",
        on_delete=models.PROTECT,
        related_name="attendance_records",
        verbose_name="Sinh viên",
    )
    checked_in_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="Thời điểm điểm danh",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo",
    )

    class Meta:
        db_table = "attendance_record"
        verbose_name = "Bản ghi điểm danh"
        verbose_name_plural = "Danh sách bản ghi điểm danh"
        ordering = ["-checked_in_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["attendance_session", "student"],
                name="att_record_session_student_uniq",
            ),
        ]
        indexes = [
            models.Index(
                fields=["student", "checked_in_at"],
                name="att_record_student_time_idx",
            ),
        ]

    def __str__(self):
        return f"{self.student.student_code} - {self.attendance_session.class_session}"
