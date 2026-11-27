import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.core.models import AuditLog

User = get_user_model()


@pytest.fixture
def audit_users(db):
    admin = User.objects.create_superuser(
        username="audit_admin",
        email="audit_admin@example.com",
        password="TestPassword123!",
    )
    student = User.objects.create_user(
        username="audit_student",
        password="TestPassword123!",
    )
    return admin, student


@pytest.mark.django_db
class TestAuditLogAPI:
    def test_admin_can_list_audit_logs(self, audit_users):
        admin, _ = audit_users

        AuditLog.objects.create(
            actor=admin,
            actor_label="Audit Admin",
            action="attendance.session.created",
            object_type="AttendanceSession",
            object_id="1",
            description="Created attendance session",
            changes={},
        )

        client = APIClient()
        client.force_authenticate(user=admin)

        response = client.get(reverse("core:audit-log-list"))

        assert response.status_code == 200
        assert len(response.data["results"]) == 1

    def test_student_cannot_access_audit_logs(self, audit_users):
        _, student = audit_users

        client = APIClient()
        client.force_authenticate(user=student)

        response = client.get(reverse("core:audit-log-list"))

        assert response.status_code == 403

    def test_anonymous_user_cannot_access_audit_logs(self):
        client = APIClient()

        response = client.get(reverse("core:audit-log-list"))

        assert response.status_code in (401, 403)

    def test_audit_log_filter_by_action(self, audit_users):
        admin, _ = audit_users

        AuditLog.objects.create(
            actor=admin,
            actor_label="Audit Admin",
            action="attendance.session.created",
            object_type="AttendanceSession",
            object_id="1",
            description="Created session",
            changes={},
        )
        AuditLog.objects.create(
            actor=admin,
            actor_label="Audit Admin",
            action="attendance.session.closed",
            object_type="AttendanceSession",
            object_id="2",
            description="Closed session",
            changes={},
        )

        client = APIClient()
        client.force_authenticate(user=admin)

        response = client.get(
            reverse("core:audit-log-list"),
            {"action": "attendance.session.created"},
        )

        assert response.status_code == 200
        results = response.data["results"]

        assert len(results) == 1
        assert results[0]["action"] == "attendance.session.created"
