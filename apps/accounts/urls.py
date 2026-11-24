from django.urls import path

from .views import (
    CampusFlowLoginView,
    CampusFlowLogoutView,
    CampusFlowPasswordChangeDoneView,
    CampusFlowPasswordChangeView,
    profile_update_view,
    profile_view,
)

app_name = "accounts"


urlpatterns = [
    path(
        "dang-nhap/",
        CampusFlowLoginView.as_view(),
        name="login",
    ),
    path(
        "dang-xuat/",
        CampusFlowLogoutView.as_view(),
        name="logout",
    ),
    path(
        "ho-so/",
        profile_view,
        name="profile",
    ),
    path(
        "ho-so/chinh-sua/",
        profile_update_view,
        name="profile_edit",
    ),
    path(
        "doi-mat-khau/",
        CampusFlowPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "doi-mat-khau/thanh-cong/",
        CampusFlowPasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
]
