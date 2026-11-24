from unittest.mock import patch

from django.db import OperationalError
from django.test import TestCase
from django.urls import reverse


class HealthCheckTests(TestCase):
    def test_health_check_returns_200(self):
        response = self.client.get(reverse("health_check"))

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json()["trang_thai"],
            "hoat_dong",
        )

        self.assertEqual(
            response.json()["co_so_du_lieu"],
            "da_ket_noi",
        )

    @patch(
        "apps.core.views.connection.ensure_connection",
        side_effect=OperationalError("Database unavailable"),
    )
    def test_health_check_returns_503_when_database_fails(
        self,
        mocked_connection,
    ):
        with self.assertLogs(
            "apps.core.views",
            level="ERROR",
        ):
            response = self.client.get(reverse("health_check"))

        self.assertEqual(response.status_code, 503)

        self.assertEqual(
            response.json()["trang_thai"],
            "khong_hoat_dong",
        )

        self.assertEqual(
            response.json()["co_so_du_lieu"],
            "khong_ket_noi",
        )

        self.assertNotIn(
            "Database unavailable",
            response.content.decode("utf-8"),
        )

        mocked_connection.assert_called_once()

    def test_health_check_only_accepts_get(self):
        response = self.client.post(reverse("health_check"))

        self.assertEqual(response.status_code, 405)
