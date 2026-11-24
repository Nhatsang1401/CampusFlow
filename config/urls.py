from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from apps.core.views import health_check

admin.site.site_header = "QUẢN TRỊ CAMPUSFLOW"
admin.site.site_title = "CampusFlow Administration"
admin.site.index_title = "Quản lý hệ thống"


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "health/",
        health_check,
        name="health_check",
    ),
    path(
        "tai-khoan/",
        include("apps.accounts.urls"),
    ),
    path(
        "",
        RedirectView.as_view(
            pattern_name="accounts:login",
            permanent=False,
        ),
        name="home",
    ),
]
