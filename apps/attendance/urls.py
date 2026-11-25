from django.urls import path

from .views import (
    AttendanceSessionCloseView,
    AttendanceSessionDetailView,
    AttendanceSessionListCreateView,
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
]
