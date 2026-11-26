from django.urls import path

from . import views

app_name = "dashboards"

urlpatterns = [
    path("", views.dashboard_index, name="index"),
    path("admin/", views.admin_dashboard, name="admin"),
    path("giang-vien/", views.lecturer_dashboard, name="lecturer"),
    path("sinh-vien/", views.student_dashboard, name="student"),
]