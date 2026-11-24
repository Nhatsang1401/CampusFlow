import logging

from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@require_GET
def health_check(request):
    """
    Check application and database availability.

    Does not expose internal exception details.
    """
    try:
        connection.ensure_connection()

    except DatabaseError:
        logger.exception("Kiểm tra kết nối cơ sở dữ liệu thất bại.")

        return JsonResponse(
            {
                "trang_thai": "khong_hoat_dong",
                "co_so_du_lieu": "khong_ket_noi",
                "thong_bao": ("Không thể kết nối cơ sở dữ liệu."),
            },
            status=503,
        )

    return JsonResponse(
        {
            "trang_thai": "hoat_dong",
            "co_so_du_lieu": "da_ket_noi",
            "phien_ban": "0.1.0",
            "thong_bao": ("Hệ thống CampusFlow đang hoạt động."),
        },
        status=200,
    )
