from django.urls import path

from . import admin_views

app_name = "admin_panel"

urlpatterns = [
    path("", admin_views.admin_panel_dashboard, name="dashboard"),
    # Tài khoản
    path("tai-khoan/", admin_views.admin_user_list, name="user_list"),
    path("tai-khoan/them/", admin_views.admin_user_create, name="user_create"),
    path(
        "tai-khoan/<int:pk>/sua/",
        admin_views.admin_user_update,
        name="user_update",
    ),
    path(
        "tai-khoan/<int:pk>/doi-trang-thai/",
        admin_views.admin_user_toggle_active,
        name="user_toggle_active",
    ),
    # Khoa
    path("khoa/", admin_views.admin_faculty_list, name="faculty_list"),
    path("khoa/them/", admin_views.admin_faculty_create, name="faculty_create"),
    path(
        "khoa/<int:pk>/sua/",
        admin_views.admin_faculty_update,
        name="faculty_update",
    ),
    # Lớp hành chính
    path("lop-hanh-chinh/", admin_views.admin_class_list, name="class_list"),
    path(
        "lop-hanh-chinh/them/",
        admin_views.admin_class_create,
        name="class_create",
    ),
    path(
        "lop-hanh-chinh/<int:pk>/sua/",
        admin_views.admin_class_update,
        name="class_update",
    ),
    # Sinh viên
    path("sinh-vien/", admin_views.admin_student_list, name="student_list"),
    path(
        "sinh-vien/them/",
        admin_views.admin_student_create,
        name="student_create",
    ),
    path(
        "sinh-vien/<int:pk>/sua/",
        admin_views.admin_student_update,
        name="student_update",
    ),
    # Giảng viên
    path("giang-vien/", admin_views.admin_lecturer_list, name="lecturer_list"),
    path(
        "giang-vien/them/",
        admin_views.admin_lecturer_create,
        name="lecturer_create",
    ),
    path(
        "giang-vien/<int:pk>/sua/",
        admin_views.admin_lecturer_update,
        name="lecturer_update",
    ),
    # Kích hoạt / ngừng hoạt động
    path(
        "<str:model_name>/<int:pk>/doi-trang-thai/",
        admin_views.admin_toggle_academic_status,
        name="academic_toggle_status",
    ),
    # Học kỳ
    path("hoc-ky/", admin_views.admin_term_list, name="term_list"),
    path("hoc-ky/them/", admin_views.admin_term_create, name="term_create"),
    path(
        "hoc-ky/<int:pk>/sua/",
        admin_views.admin_term_update,
        name="term_update",
    ),
    # Học phần
    path("hoc-phan/", admin_views.admin_course_list, name="course_list"),
    path("hoc-phan/them/", admin_views.admin_course_create, name="course_create"),
    path(
        "hoc-phan/<int:pk>/sua/",
        admin_views.admin_course_update,
        name="course_update",
    ),
    # Lớp học phần
    path(
        "lop-hoc-phan/",
        admin_views.admin_course_section_list,
        name="course_section_list",
    ),
    path(
        "lop-hoc-phan/them/",
        admin_views.admin_course_section_create,
        name="course_section_create",
    ),
    path(
        "lop-hoc-phan/<int:pk>/sua/",
        admin_views.admin_course_section_update,
        name="course_section_update",
    ),
    # Đăng ký học phần
    path(
        "dang-ky-hoc-phan/",
        admin_views.admin_enrollment_list,
        name="enrollment_list",
    ),
    path(
        "dang-ky-hoc-phan/<int:pk>/doi-trang-thai/",
        admin_views.admin_enrollment_change_status,
        name="enrollment_change_status",
    ),
    path("phong-hoc/", admin_views.admin_classroom_list, name="classroom_list"),
    path("phong-hoc/them/", admin_views.admin_classroom_create, name="classroom_create"),
    path("phong-hoc/<int:pk>/sua/", admin_views.admin_classroom_update, name="classroom_update"),
    path(
        "phong-hoc/<int:pk>/trang-thai/",
        admin_views.admin_classroom_toggle_active,
        name="classroom_toggle_active",
    ),
    path("thoi-khoa-bieu/", admin_views.admin_timetable_list, name="timetable_list"),
    path("thoi-khoa-bieu/them/", admin_views.admin_timetable_create, name="timetable_create"),
    path(
        "thoi-khoa-bieu/<int:pk>/sua/",
        admin_views.admin_timetable_update,
        name="timetable_update",
    ),
    path("buoi-hoc/", admin_views.admin_class_session_list, name="class_session_list"),
    path("buoi-hoc/them/", admin_views.admin_class_session_create, name="class_session_create"),
    path(
        "buoi-hoc/<int:pk>/sua/",
        admin_views.admin_class_session_update,
        name="class_session_update",
    ),
    path("nhat-ky/", admin_views.admin_audit_log_list, name="audit_log_list"),
]
