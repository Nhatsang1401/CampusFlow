from django.conf import settings
from django.db import models
from django.utils import timezone


class NotificationType(models.TextChoices):
    INFO = "info", "Thông tin"
    SUCCESS = "success", "Thành công"
    WARNING = "warning", "Cảnh báo"
    ERROR = "error", "Lỗi"


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Người nhận",
    )
    title = models.CharField(max_length=150, verbose_name="Tiêu đề")
    message = models.TextField(verbose_name="Nội dung")
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        db_index=True,
        verbose_name="Loại thông báo",
    )
    link = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Liên kết nội bộ",
    )
    is_read = models.BooleanField(default=False, db_index=True, verbose_name="Đã đọc")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Thời điểm đọc")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "core_notification"
        verbose_name = "Thông báo"
        verbose_name_plural = "Danh sách thông báo"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["recipient", "is_read", "-created_at"],
                name="core_notif_rec_read_idx",
            ),
        ]

    def mark_as_read(self):
        if self.is_read:
            return False

        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=["is_read", "read_at"])
        return True

    def __str__(self):
        return f"{self.recipient} - {self.title}"


class ImmutableAuditQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise TypeError("AuditLog không cho phép cập nhật.")

    def delete(self):
        raise TypeError("AuditLog không cho phép xóa.")


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="Người thực hiện",
    )
    actor_label = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Tên người thực hiện tại thời điểm ghi nhận",
    )
    action = models.CharField(max_length=100, db_index=True, verbose_name="Hành động")
    object_type = models.CharField(max_length=100, db_index=True, verbose_name="Loại đối tượng")
    object_id = models.CharField(max_length=64, blank=True, default="", verbose_name="ID đối tượng")
    description = models.CharField(max_length=255, blank=True, default="", verbose_name="Mô tả")
    changes = models.JSONField(default=dict, blank=True, verbose_name="Dữ liệu thay đổi")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Địa chỉ IP")
    user_agent = models.CharField(max_length=500, blank=True, default="", verbose_name="User-Agent")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = ImmutableAuditQuerySet.as_manager()

    class Meta:
        db_table = "core_audit_log"
        verbose_name = "Nhật ký kiểm toán"
        verbose_name_plural = "Nhật ký kiểm toán"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["object_type", "object_id"],
                name="core_audit_object_idx",
            ),
            models.Index(
                fields=["actor", "-created_at"],
                name="core_audit_actor_time_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise TypeError("AuditLog không cho phép cập nhật bản ghi đã tồn tại.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise TypeError("AuditLog không cho phép xóa.")

    def __str__(self):
        return f"{self.action} - {self.object_type}#{self.object_id}"
