from rest_framework import serializers

from .models import AttendanceRecord, AttendanceSession


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


class StudentCheckInSerializer(serializers.Serializer):
    token = serializers.CharField(
        max_length=256,
        trim_whitespace=True,
        write_only=True,
    )


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_code = serializers.CharField(
        source="student.student_code",
        read_only=True,
    )
    course_code = serializers.CharField(
        source="attendance_session.class_session.timetable.course_section.course.code",
        read_only=True,
    )
    course_name = serializers.CharField(
        source="attendance_session.class_session.timetable.course_section.course.name",
        read_only=True,
    )
    section_code = serializers.CharField(
        source="attendance_session.class_session.timetable.course_section.code",
        read_only=True,
    )
    session_date = serializers.DateField(
        source="attendance_session.class_session.session_date",
        read_only=True,
    )

    class Meta:
        model = AttendanceRecord
        fields = [
            "id",
            "student_code",
            "course_code",
            "course_name",
            "section_code",
            "session_date",
            "checked_in_at",
            "created_at",
        ]
        read_only_fields = fields
