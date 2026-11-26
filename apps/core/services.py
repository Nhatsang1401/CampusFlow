from apps.core.models import AuditLog, Notification, NotificationType


def _get_actor_label(actor):
    if actor is None:
        return ""

    full_name = f"{actor.last_name} {actor.first_name}".strip()
    return full_name or actor.get_username()


def _get_request_metadata(request):
    if request is None:
        return None, ""

    # Không tin X-Forwarded-For trừ khi ứng dụng được triển khai
    # sau trusted proxy đã cấu hình đúng.
    ip_address = request.META.get("REMOTE_ADDR")
    user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
    return ip_address or None, user_agent


def create_notification(
    *,
    recipient,
    title,
    message,
    notification_type=NotificationType.INFO,
    link="",
):
    if not recipient or not recipient.is_active:
        return None

    return Notification.objects.create(
        recipient=recipient,
        title=title[:150],
        message=message,
        notification_type=notification_type,
        link=link[:500],
    )


def create_notifications(
    *,
    recipients,
    title,
    message,
    notification_type=NotificationType.INFO,
    link="",
):
    """Create the same notification for multiple active recipients."""
    active_recipients = [user for user in recipients if user and user.is_active]

    if not active_recipients:
        return 0

    Notification.objects.bulk_create(
        [
            Notification(
                recipient=user,
                title=title[:150],
                message=message,
                notification_type=notification_type,
                link=link[:500],
            )
            for user in active_recipients
        ],
        batch_size=500,
    )
    return len(active_recipients)


def create_audit_log(
    *,
    actor,
    action,
    object_type,
    object_id="",
    description="",
    changes=None,
    request=None,
):
    ip_address, user_agent = _get_request_metadata(request)

    return AuditLog.objects.create(
        actor=actor,
        actor_label=_get_actor_label(actor),
        action=action[:100],
        object_type=object_type[:100],
        object_id=str(object_id)[:64],
        description=description[:255],
        changes=changes or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
