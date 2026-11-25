from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AttendanceSession
from .permissions import IsLecturerOrAdmin
from .serializers import (
    AttendanceSessionCreateSerializer,
    AttendanceSessionSerializer,
)
from .services import (
    close_attendance_session,
    create_attendance_session,
    generate_qr_base64,
)


class AttendanceSessionListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsLecturerOrAdmin]

    def get_queryset(self, request):
        queryset = AttendanceSession.objects.select_related(
            "class_session",
            "class_session__timetable",
            "class_session__timetable__course_section",
        ).order_by("-created_at")

        if not request.user.is_superuser:
            queryset = queryset.filter(
                class_session__timetable__course_section__lecturer__user=request.user
            )

        return queryset

    def get(self, request):
        queryset = self.get_queryset(request)

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)

        serializer = AttendanceSessionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = AttendanceSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            session, token = create_attendance_session(
                class_session_id=serializer.validated_data["class_session_id"],
                user=request.user,
                duration_minutes=serializer.validated_data["duration_minutes"],
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages) from exc

        return Response(
            {
                "session": AttendanceSessionSerializer(session).data,
                "token": token,
                "qr_code": generate_qr_base64(token),
            },
            status=status.HTTP_201_CREATED,
        )


class AttendanceSessionDetailView(APIView):
    permission_classes = [IsAuthenticated, IsLecturerOrAdmin]

    def get_object(self, request, pk):
        queryset = AttendanceSession.objects.select_related(
            "class_session__timetable__course_section__lecturer",
        )

        if not request.user.is_superuser:
            queryset = queryset.filter(
                class_session__timetable__course_section__lecturer__user=request.user
            )

        return get_object_or_404(queryset, pk=pk)

    def get(self, request, pk):
        session = self.get_object(request, pk)
        return Response(AttendanceSessionSerializer(session).data)


class AttendanceSessionCloseView(APIView):
    permission_classes = [IsAuthenticated, IsLecturerOrAdmin]

    def post(self, request, pk):
        try:
            session = close_attendance_session(
                session_id=pk,
                user=request.user,
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages) from exc

        return Response(AttendanceSessionSerializer(session).data)
