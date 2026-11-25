from django.urls import path

from .views import (
    AttendanceSessionCloseView,
    AttendanceSessionDetailView,
    AttendanceSessionListCreateView,
    MyAttendanceRecordsView,
    StudentCheckInView,
)

app_name = "attendance"

urlpatterns = [
    path(
        "sessions/",
        AttendanceSessionListCreateView.as_view(),
        name="session-list-create",
    ),
    path(
        "sessions/<int:pk>/",
        AttendanceSessionDetailView.as_view(),
        name="session-detail",
    ),
    path(
        "sessions/<int:pk>/close/",
        AttendanceSessionCloseView.as_view(),
        name="session-close",
    ),
    path(
        "check-in/",
        StudentCheckInView.as_view(),
        name="check-in",
    ),
    path(
        "my-records/",
        MyAttendanceRecordsView.as_view(),
        name="my-records",
    ),
]
