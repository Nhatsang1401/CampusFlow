import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.core.models import Notification

User = get_user_model()


@pytest.fixture
def notification_users(db):
    user1 = User.objects.create_user(
        username="notification_student_1",
        password="TestPassword123!",
    )
    user2 = User.objects.create_user(
        username="notification_student_2",
        password="TestPassword123!",
    )
    return user1, user2


@pytest.fixture
def notification_client():
    return APIClient()


@pytest.mark.django_db
class TestNotificationAPI:
    def test_user_only_sees_own_notifications(self, notification_users, notification_client):
        user1, user2 = notification_users

        own_notification = Notification.objects.create(
            recipient=user1,
            title="Thông báo của tôi",
            message="Nội dung dành cho tôi",
        )
        Notification.objects.create(
            recipient=user2,
            title="Thông báo người khác",
            message="Không được phép xem",
        )

        notification_client.force_authenticate(user=user1)
        response = notification_client.get(reverse("core:notification-list"))

        assert response.status_code == 200

        results = response.data["results"]
        returned_ids = [item["id"] for item in results]

        assert own_notification.id in returned_ids
        assert len(results) == 1

    def test_anonymous_user_cannot_list_notifications(self, notification_client):
        response = notification_client.get(reverse("core:notification-list"))

        assert response.status_code in (401, 403)

    def test_unread_count_only_counts_current_user_notifications(
        self, notification_users, notification_client
    ):
        user1, user2 = notification_users

        Notification.objects.create(
            recipient=user1,
            title="Unread 1",
            message="Message 1",
        )
        Notification.objects.create(
            recipient=user1,
            title="Unread 2",
            message="Message 2",
        )
        Notification.objects.create(
            recipient=user2,
            title="Other user",
            message="Message",
        )

        notification_client.force_authenticate(user=user1)
        response = notification_client.get(reverse("core:notification-unread-count"))

        assert response.status_code == 200
        assert response.data["unread_count"] == 2

    def test_unread_filter_returns_only_unread_notifications(
        self, notification_users, notification_client
    ):
        user1, _ = notification_users

        unread = Notification.objects.create(
            recipient=user1,
            title="Unread",
            message="Unread message",
        )
        read = Notification.objects.create(
            recipient=user1,
            title="Read",
            message="Read message",
            is_read=True,
        )

        notification_client.force_authenticate(user=user1)
        response = notification_client.get(
            reverse("core:notification-list"),
            {"unread": "true"},
        )

        assert response.status_code == 200

        returned_ids = [item["id"] for item in response.data["results"]]

        assert unread.id in returned_ids
        assert read.id not in returned_ids

    def test_user_can_mark_own_notification_as_read(self, notification_users, notification_client):
        user1, _ = notification_users

        notification = Notification.objects.create(
            recipient=user1,
            title="Read me",
            message="Notification message",
        )

        notification_client.force_authenticate(user=user1)
        response = notification_client.post(f"/api/core/notifications/{notification.pk}/read/")

        assert response.status_code == 200

        notification.refresh_from_db()
        assert notification.is_read is True
        assert notification.read_at is not None

    def test_user_cannot_mark_other_users_notification_as_read(
        self, notification_users, notification_client
    ):
        user1, user2 = notification_users

        notification = Notification.objects.create(
            recipient=user2,
            title="Private notification",
            message="Message",
        )

        notification_client.force_authenticate(user=user1)
        response = notification_client.post(f"/api/core/notifications/{notification.pk}/read/")

        assert response.status_code == 404

        notification.refresh_from_db()
        assert notification.is_read is False

    def test_user_can_mark_all_notifications_as_read(self, notification_users, notification_client):
        user1, user2 = notification_users

        Notification.objects.create(
            recipient=user1,
            title="First",
            message="First message",
        )
        Notification.objects.create(
            recipient=user1,
            title="Second",
            message="Second message",
        )
        other_notification = Notification.objects.create(
            recipient=user2,
            title="Other",
            message="Other message",
        )

        notification_client.force_authenticate(user=user1)
        response = notification_client.post("/api/core/notifications/read-all/")

        assert response.status_code == 200
        assert (
            Notification.objects.filter(
                recipient=user1,
                is_read=False,
            ).count()
            == 0
        )

        other_notification.refresh_from_db()
        assert other_notification.is_read is False
