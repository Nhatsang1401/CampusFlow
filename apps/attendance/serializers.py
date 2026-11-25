from rest_framework import serializers

from .models import AttendanceSession


class AttendanceSessionCreateSerializer(serializers.Serializer):
    class_session_id = serializers.IntegerField(min_value=1)
    duration_minutes = serializers.IntegerField(
        min_value=1,
        max_value=120,
        default=5,
    )


class AttendanceSessionSerializer(serializers.ModelSerializer):
    class_session_id = serializers.IntegerField(read_only=True)
    display_status = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = AttendanceSession
        fields = [
            "id",
            "class_session_id",
            "starts_at",
            "expires_at",
            "status",
            "display_status",
            "is_active",
            "created_at",
        ]
        read_only_fields = fields
