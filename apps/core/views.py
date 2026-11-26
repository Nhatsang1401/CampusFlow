import logging

from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AuditLog, Notification
from .permissions import IsAdministrator
from .serializers import AuditLogSerializer, NotificationSerializer

logger = logging.getLogger(__name__)


@require_GET
def health_check(request):
    """Check application and database availability."""
    try:
        connection.ensure_connection()
    except DatabaseError:
        logger.exception("Kiểm tra kết nối cơ sở dữ liệu thất bại.")
        return JsonResponse(
            {
                "trang_thai": "khong_hoat_dong",
                "co_so_du_lieu": "khong_ket_noi",
                "thong_bao": "Không thể kết nối cơ sở dữ liệu.",
            },
            status=503,
        )

    return JsonResponse(
        {
            "trang_thai": "hoat_dong",
            "co_so_du_lieu": "da_ket_noi",
            "phien_ban": "0.1.0",
            "thong_bao": "Hệ thống CampusFlow đang hoạt động.",
        },
        status=200,
    )


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Notification.objects.filter(
            recipient=request.user,
        ).order_by("-created_at")

        unread_only = request.query_params.get("unread")
        if unread_only is not None:
            if unread_only.lower() not in {"true", "false", "1", "0"}:
                raise ValidationError({"unread": "Giá trị phải là true hoặc false."})

            if unread_only.lower() in {"true", "1"}:
                queryset = queryset.filter(is_read=False)

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()

        return Response({"unread_count": count})


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        notification = Notification.objects.filter(
            recipient=request.user,
            pk=pk,
        ).first()

        if notification is None:
            return Response(
                {"detail": "Không tìm thấy thông báo."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])

        return Response(NotificationSerializer(notification).data)


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        now = timezone.now()

        updated_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(
            is_read=True,
            read_at=now,
        )

        return Response({"updated_count": updated_count})


class AuditLogListView(APIView):
    permission_classes = [IsAuthenticated, IsAdministrator]

    def get(self, request):
        queryset = AuditLog.objects.select_related("actor").all()

        action = request.query_params.get("action")
        if action:
            queryset = queryset.filter(action=action[:100])

        object_type = request.query_params.get("object_type")
        if object_type:
            queryset = queryset.filter(object_type=object_type[:100])

        actor_id = request.query_params.get("actor_id")
        if actor_id:
            if not actor_id.isdigit():
                raise ValidationError({"actor_id": "ID người thực hiện không hợp lệ."})
            queryset = queryset.filter(actor_id=int(actor_id))

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = AuditLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
