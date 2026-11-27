from datetime import date

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.academics.models import (
    AcademicClass,
    AcademicTerm,
    Classroom,
    ClassroomType,
    ClassSession,
    ClassSessionStatus,
    Course,
    CourseSection,
    Enrollment,
    EnrollmentStatus,
    Faculty,
    LecturerProfile,
    StudentProfile,
    Timetable,
    Weekday,
)
from apps.core.models import AuditLog
from apps.core.services import create_audit_log

from .admin_forms import (
    AdminAcademicClassForm,
    AdminAcademicTermForm,
    AdminClassroomForm,
    AdminClassSessionForm,
    AdminCourseForm,
    AdminCourseSectionForm,
    AdminFacultyForm,
    AdminLecturerProfileForm,
    AdminStudentProfileForm,
    AdminTimetableForm,
    AdminUserCreateForm,
    AdminUserUpdateForm,
)
from .admin_services import (
    change_enrollment_status,
    get_academic_class_queryset,
    get_academic_term_queryset,
    get_admin_panel_overview,
    get_admin_user_queryset,
    get_audit_log_queryset,
    get_class_session_queryset,
    get_classroom_queryset,
    get_course_queryset,
    get_course_section_queryset,
    get_enrollment_queryset,
    get_faculty_queryset,
    get_lecturer_profile_queryset,
    get_student_profile_queryset,
    get_timetable_queryset,
)

User = get_user_model()


def is_campusflow_admin(user):
    return user.is_authenticated and user.is_active and user.is_superuser


admin_required = user_passes_test(
    is_campusflow_admin,
    login_url="accounts:login",
)


@admin_required
def admin_panel_dashboard(request):
    return render(
        request,
        "admin_panel/dashboard.html",
        get_admin_panel_overview(),
    )


@admin_required
def admin_user_list(request):
    query = request.GET.get("q", "").strip()[:100]
    role = request.GET.get("role", "").strip()
    active = request.GET.get("active", "").strip()

    users = get_admin_user_queryset(
        query=query,
        role=role,
        active=active,
    )

    paginator = Paginator(users, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "admin_panel/users/list.html",
        {
            "page_obj": page_obj,
            "query": query,
            "selected_role": role,
            "selected_active": active,
        },
    )


@admin_required
def admin_user_create(request):
    if request.method == "POST":
        form = AdminUserCreateForm(request.POST)

        if form.is_valid():
            user = form.save()
            create_audit_log(
                actor=request.user,
                action="admin.user.created",
                object_type="User",
                object_id=user.pk,
                description=f"Tạo tài khoản {user.username}.",
                changes={
                    "role": user.role,
                    "is_active": user.is_active,
                    "is_staff": user.is_staff,
                },
                request=request,
            )

            messages.success(
                request,
                f"Đã tạo tài khoản {user.username} thành công.",
            )
            return redirect("admin_panel:user_list")
    else:
        form = AdminUserCreateForm()

    return render(
        request,
        "admin_panel/users/form.html",
        {
            "form": form,
            "page_title": "Tạo tài khoản",
            "submit_label": "Tạo tài khoản",
        },
    )


@admin_required
def admin_user_update(request, pk):
    user = get_object_or_404(
        User.objects.filter(is_superuser=False),
        pk=pk,
    )

    if request.method == "POST":
        form = AdminUserUpdateForm(request.POST, instance=user)

        if form.is_valid():
            old_values = {
                "role": user.role,
                "is_active": user.is_active,
                "is_staff": user.is_staff,
            }
            form.save()
            create_audit_log(
                actor=request.user,
                action="admin.user.updated",
                object_type="User",
                object_id=user.pk,
                description=f"Cập nhật tài khoản {user.username}.",
                changes={
                    "before": old_values,
                    "after": {
                        "role": user.role,
                        "is_active": user.is_active,
                        "is_staff": user.is_staff,
                    },
                },
                request=request,
            )
            messages.success(
                request,
                f"Đã cập nhật tài khoản {user.username}.",
            )
            return redirect("admin_panel:user_list")
    else:
        form = AdminUserUpdateForm(instance=user)

    return render(
        request,
        "admin_panel/users/form.html",
        {
            "form": form,
            "page_title": f"Cập nhật {user.username}",
            "submit_label": "Lưu thay đổi",
            "editing": True,
        },
    )


@admin_required
@require_POST
def admin_user_toggle_active(request, pk):
    user = get_object_or_404(
        User.objects.filter(is_superuser=False),
        pk=pk,
    )

    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    create_audit_log(
        actor=request.user,
        action="admin.user.status_changed",
        object_type="User",
        object_id=user.pk,
        description=f"Thay đổi trạng thái tài khoản {user.username}.",
        changes={"is_active": user.is_active},
        request=request,
    )
    state = "mở khóa" if user.is_active else "khóa"

    messages.success(
        request,
        f"Đã {state} tài khoản {user.username}.",
    )

    return redirect("admin_panel:user_list")


def _admin_list(request, queryset, template, context=None):
    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    data = {"page_obj": page_obj}
    if context:
        data.update(context)
    return render(request, template, data)


def _audit_admin_change(request, action, obj, description, changes=None):
    create_audit_log(
        actor=request.user,
        action=action,
        object_type=obj.__class__.__name__,
        object_id=obj.pk,
        description=description,
        changes=changes or {},
        request=request,
    )


@admin_required
def admin_faculty_list(request):
    query = request.GET.get("q", "").strip()[:100]
    active = request.GET.get("active", "").strip()
    queryset = get_faculty_queryset(query=query, active=active)
    return _admin_list(
        request,
        queryset,
        "admin_panel/academic/list.html",
        {
            "page_title": "Quản lý khoa",
            "create_url": "admin_panel:faculty_create",
            "edit_url": "admin_panel:faculty_update",
            "query": query,
            "selected_active": active,
            "list_type": "faculty",
        },
    )


@admin_required
def admin_faculty_create(request):
    form = AdminFacultyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            obj = form.save()
            _audit_admin_change(
                request,
                "admin.faculty.created",
                obj,
                f"Tạo khoa {obj.code}.",
                {"code": obj.code, "name": obj.name},
            )
        messages.success(request, "Đã tạo khoa thành công.")
        return redirect("admin_panel:faculty_list")
    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": "Thêm khoa",
            "back_url": "admin_panel:faculty_list",
        },
    )


@admin_required
def admin_faculty_update(request, pk):
    obj = get_object_or_404(Faculty, pk=pk)
    form = AdminFacultyForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        before = {"code": obj.code, "name": obj.name, "is_active": obj.is_active}
        with transaction.atomic():
            obj = form.save()
            _audit_admin_change(
                request,
                "admin.faculty.updated",
                obj,
                f"Cập nhật khoa {obj.code}.",
                {
                    "before": before,
                    "after": {
                        "code": obj.code,
                        "name": obj.name,
                        "is_active": obj.is_active,
                    },
                },
            )
        messages.success(request, "Đã cập nhật khoa.")
        return redirect("admin_panel:faculty_list")
    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": f"Cập nhật khoa: {obj.code}",
            "back_url": "admin_panel:faculty_list",
        },
    )


@admin_required
def admin_class_list(request):
    query = request.GET.get("q", "").strip()[:100]
    faculty = request.GET.get("faculty", "").strip()
    active = request.GET.get("active", "").strip()
    queryset = get_academic_class_queryset(query=query, faculty=faculty, active=active)
    return _admin_list(
        request,
        queryset,
        "admin_panel/academic/list.html",
        {
            "page_title": "Quản lý lớp hành chính",
            "create_url": "admin_panel:class_create",
            "edit_url": "admin_panel:class_update",
            "query": query,
            "selected_faculty": faculty,
            "selected_active": active,
            "faculties": Faculty.objects.order_by("code"),
            "list_type": "class",
        },
    )


@admin_required
def admin_class_create(request):
    form = AdminAcademicClassForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            obj = form.save()
            _audit_admin_change(
                request,
                "admin.academic_class.created",
                obj,
                f"Tạo lớp hành chính {obj.code}.",
                {"code": obj.code, "faculty_id": obj.faculty_id},
            )
        messages.success(request, "Đã tạo lớp hành chính.")
        return redirect("admin_panel:class_list")
    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": "Thêm lớp hành chính",
            "back_url": "admin_panel:class_list",
        },
    )


@admin_required
def admin_class_update(request, pk):
    obj = get_object_or_404(AcademicClass, pk=pk)
    form = AdminAcademicClassForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        before = {
            "code": obj.code,
            "faculty_id": obj.faculty_id,
            "is_active": obj.is_active,
        }
        with transaction.atomic():
            obj = form.save()
            _audit_admin_change(
                request,
                "admin.academic_class.updated",
                obj,
                f"Cập nhật lớp hành chính {obj.code}.",
                {
                    "before": before,
                    "after": {
                        "code": obj.code,
                        "faculty_id": obj.faculty_id,
                        "is_active": obj.is_active,
                    },
                },
            )
        messages.success(request, "Đã cập nhật lớp hành chính.")
        return redirect("admin_panel:class_list")
    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": f"Cập nhật lớp: {obj.code}",
            "back_url": "admin_panel:class_list",
        },
    )


@admin_required
def admin_student_list(request):
    query = request.GET.get("q", "").strip()[:100]
    faculty = request.GET.get("faculty", "").strip()
    academic_class = request.GET.get("class", "").strip()
    queryset = get_student_profile_queryset(
        query=query, faculty=faculty, academic_class=academic_class
    )
    return _admin_list(
        request,
        queryset,
        "admin_panel/academic/list.html",
        {
            "page_title": "Quản lý sinh viên",
            "create_url": "admin_panel:student_create",
            "edit_url": "admin_panel:student_update",
            "query": query,
            "selected_faculty": faculty,
            "selected_class": academic_class,
            "faculties": Faculty.objects.order_by("code"),
            "classes": AcademicClass.objects.order_by("code"),
            "list_type": "student",
        },
    )


@admin_required
def admin_student_create(request):
    form = AdminStudentProfileForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            obj = form.save()
            _audit_admin_change(
                request,
                "admin.student_profile.created",
                obj,
                f"Tạo hồ sơ sinh viên {obj.student_code}.",
                {"student_code": obj.student_code, "user_id": obj.user_id},
            )
        messages.success(request, "Đã tạo hồ sơ sinh viên.")
        return redirect("admin_panel:student_list")
    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": "Thêm sinh viên",
            "back_url": "admin_panel:student_list",
        },
    )


@admin_required
def admin_student_update(request, pk):
    obj = get_object_or_404(StudentProfile, pk=pk)
    form = AdminStudentProfileForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        before = {
            "student_code": obj.student_code,
            "user_id": obj.user_id,
            "academic_class_id": obj.academic_class_id,
        }
        with transaction.atomic():
            obj = form.save()
            _audit_admin_change(
                request,
                "admin.student_profile.updated",
                obj,
                f"Cập nhật hồ sơ sinh viên {obj.student_code}.",
                {
                    "before": before,
                    "after": {
                        "student_code": obj.student_code,
                        "user_id": obj.user_id,
                        "academic_class_id": obj.academic_class_id,
                    },
                },
            )
        messages.success(request, "Đã cập nhật hồ sơ sinh viên.")
        return redirect("admin_panel:student_list")
    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": f"Cập nhật sinh viên: {obj.student_code}",
            "back_url": "admin_panel:student_list",
        },
    )


@admin_required
def admin_lecturer_list(request):
    query = request.GET.get("q", "").strip()[:100]
    faculty = request.GET.get("faculty", "").strip()
    queryset = get_lecturer_profile_queryset(query=query, faculty=faculty)
    return _admin_list(
        request,
        queryset,
        "admin_panel/academic/list.html",
        {
            "page_title": "Quản lý giảng viên",
            "create_url": "admin_panel:lecturer_create",
            "edit_url": "admin_panel:lecturer_update",
            "query": query,
            "selected_faculty": faculty,
            "faculties": Faculty.objects.order_by("code"),
            "list_type": "lecturer",
        },
    )


@admin_required
def admin_lecturer_create(request):
    form = AdminLecturerProfileForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            obj = form.save()
            _audit_admin_change(
                request,
                "admin.lecturer_profile.created",
                obj,
                f"Tạo hồ sơ giảng viên {obj.lecturer_code}.",
                {"lecturer_code": obj.lecturer_code, "user_id": obj.user_id},
            )
        messages.success(request, "Đã tạo hồ sơ giảng viên.")
        return redirect("admin_panel:lecturer_list")
    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": "Thêm giảng viên",
            "back_url": "admin_panel:lecturer_list",
        },
    )


@admin_required
def admin_lecturer_update(request, pk):
    obj = get_object_or_404(LecturerProfile, pk=pk)
    form = AdminLecturerProfileForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        before = {
            "lecturer_code": obj.lecturer_code,
            "user_id": obj.user_id,
            "faculty_id": obj.faculty_id,
        }
        with transaction.atomic():
            obj = form.save()
            _audit_admin_change(
                request,
                "admin.lecturer_profile.updated",
                obj,
                f"Cập nhật hồ sơ giảng viên {obj.lecturer_code}.",
                {
                    "before": before,
                    "after": {
                        "lecturer_code": obj.lecturer_code,
                        "user_id": obj.user_id,
                        "faculty_id": obj.faculty_id,
                    },
                },
            )
        messages.success(request, "Đã cập nhật hồ sơ giảng viên.")
        return redirect("admin_panel:lecturer_list")
    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": f"Cập nhật giảng viên: {obj.lecturer_code}",
            "back_url": "admin_panel:lecturer_list",
        },
    )


@admin_required
@require_POST
def admin_toggle_academic_status(request, model_name, pk):
    model_map = {
        "faculty": Faculty,
        "class": AcademicClass,
    }
    model = model_map.get(model_name)
    if model is None:
        return HttpResponseNotAllowed(["POST"])

    obj = get_object_or_404(model, pk=pk)
    obj.is_active = not obj.is_active
    obj.save(update_fields=["is_active", "updated_at"])
    _audit_admin_change(
        request,
        f"admin.{model_name}.status_changed",
        obj,
        f"Thay đổi trạng thái {obj}.",
        {"is_active": obj.is_active},
    )
    messages.success(
        request,
        f"Đã {'kích hoạt' if obj.is_active else 'ngừng hoạt động'} {obj}.",
    )
    return redirect(
        "admin_panel:faculty_list" if model_name == "faculty" else "admin_panel:class_list"
    )


# =========================================================
# QUẢN LÝ HỌC KỲ
# =========================================================


@admin_required
def admin_term_list(request):
    query = request.GET.get("q", "").strip()[:100]
    active = request.GET.get("active", "").strip()

    queryset = get_academic_term_queryset(
        query=query,
        active=active,
    )

    return _admin_list(
        request,
        queryset,
        "admin_panel/academic/list.html",
        {
            "page_title": "Quản lý học kỳ",
            "create_url": "admin_panel:term_create",
            "edit_url": "admin_panel:term_update",
            "query": query,
            "selected_active": active,
            "list_type": "term",
        },
    )


@admin_required
def admin_term_create(request):
    form = AdminAcademicTermForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            obj = form.save()

            _audit_admin_change(
                request,
                "admin.academic_term.created",
                obj,
                f"Tạo học kỳ {obj.code}.",
                {
                    "code": obj.code,
                    "name": obj.name,
                    "academic_year": obj.academic_year,
                    "semester": obj.semester,
                },
            )

        messages.success(request, "Đã tạo học kỳ thành công.")
        return redirect("admin_panel:term_list")

    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": "Thêm học kỳ",
            "back_url": "admin_panel:term_list",
        },
    )


@admin_required
def admin_term_update(request, pk):
    obj = get_object_or_404(AcademicTerm, pk=pk)

    form = AdminAcademicTermForm(
        request.POST or None,
        instance=obj,
    )

    if request.method == "POST" and form.is_valid():
        before = {
            "code": obj.code,
            "name": obj.name,
            "is_active": obj.is_active,
        }

        with transaction.atomic():
            obj = form.save()

            _audit_admin_change(
                request,
                "admin.academic_term.updated",
                obj,
                f"Cập nhật học kỳ {obj.code}.",
                {
                    "before": before,
                    "after": {
                        "code": obj.code,
                        "name": obj.name,
                        "is_active": obj.is_active,
                    },
                },
            )

        messages.success(request, "Đã cập nhật học kỳ.")
        return redirect("admin_panel:term_list")

    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": f"Cập nhật học kỳ: {obj.code}",
            "back_url": "admin_panel:term_list",
        },
    )


# =========================================================
# QUẢN LÝ HỌC PHẦN
# =========================================================


@admin_required
def admin_course_list(request):
    query = request.GET.get("q", "").strip()[:100]
    active = request.GET.get("active", "").strip()

    queryset = get_course_queryset(
        query=query,
        active=active,
    )

    return _admin_list(
        request,
        queryset,
        "admin_panel/academic/list.html",
        {
            "page_title": "Quản lý học phần",
            "create_url": "admin_panel:course_create",
            "edit_url": "admin_panel:course_update",
            "query": query,
            "selected_active": active,
            "list_type": "course",
        },
    )


@admin_required
def admin_course_create(request):
    form = AdminCourseForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            obj = form.save()

            _audit_admin_change(
                request,
                "admin.course.created",
                obj,
                f"Tạo học phần {obj.code}.",
                {
                    "code": obj.code,
                    "name": obj.name,
                    "credits": obj.credits,
                },
            )

        messages.success(request, "Đã tạo học phần thành công.")
        return redirect("admin_panel:course_list")

    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": "Thêm học phần",
            "back_url": "admin_panel:course_list",
        },
    )


@admin_required
def admin_course_update(request, pk):
    obj = get_object_or_404(Course, pk=pk)

    form = AdminCourseForm(
        request.POST or None,
        instance=obj,
    )

    if request.method == "POST" and form.is_valid():
        before = {
            "code": obj.code,
            "name": obj.name,
            "credits": obj.credits,
            "is_active": obj.is_active,
        }

        with transaction.atomic():
            obj = form.save()

            _audit_admin_change(
                request,
                "admin.course.updated",
                obj,
                f"Cập nhật học phần {obj.code}.",
                {
                    "before": before,
                    "after": {
                        "code": obj.code,
                        "name": obj.name,
                        "credits": obj.credits,
                        "is_active": obj.is_active,
                    },
                },
            )

        messages.success(request, "Đã cập nhật học phần.")
        return redirect("admin_panel:course_list")

    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": f"Cập nhật học phần: {obj.code}",
            "back_url": "admin_panel:course_list",
        },
    )


@admin_required
def admin_course_section_list(request):
    query = request.GET.get("q", "").strip()[:100]
    term = request.GET.get("term", "").strip()
    course = request.GET.get("course", "").strip()
    lecturer = request.GET.get("lecturer", "").strip()
    active = request.GET.get("active", "").strip()

    queryset = get_course_section_queryset(
        query=query,
        term=term,
        course=course,
        lecturer=lecturer,
        active=active,
    )

    return _admin_list(
        request,
        queryset,
        "admin_panel/course_sections/list.html",
        {
            "page_title": "Quản lý lớp học phần",
            "query": query,
            "selected_term": term,
            "selected_course": course,
            "selected_lecturer": lecturer,
            "selected_active": active,
            "terms": AcademicTerm.objects.order_by("-academic_year", "semester"),
            "courses": Course.objects.order_by("code"),
            "lecturers": LecturerProfile.objects.select_related("user").order_by("lecturer_code"),
        },
    )


@admin_required
def admin_course_section_create(request):
    form = AdminCourseSectionForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            obj = form.save()
            _audit_admin_change(
                request,
                "admin.course_section.created",
                obj,
                f"Tạo lớp học phần {obj.code}.",
                {
                    "code": obj.code,
                    "course_id": obj.course_id,
                    "term_id": obj.term_id,
                    "lecturer_id": obj.lecturer_id,
                    "max_students": obj.max_students,
                },
            )

        messages.success(request, "Đã tạo lớp học phần thành công.")
        return redirect("admin_panel:course_section_list")

    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": "Thêm lớp học phần",
            "back_url": "admin_panel:course_section_list",
        },
    )


@admin_required
def admin_course_section_update(request, pk):
    obj = get_object_or_404(
        CourseSection.objects.select_related("course", "term", "lecturer"),
        pk=pk,
    )

    form = AdminCourseSectionForm(request.POST or None, instance=obj)

    if request.method == "POST" and form.is_valid():
        before = {
            "code": obj.code,
            "course_id": obj.course_id,
            "term_id": obj.term_id,
            "lecturer_id": obj.lecturer_id,
            "max_students": obj.max_students,
            "registration_open": obj.registration_open,
            "is_active": obj.is_active,
        }

        with transaction.atomic():
            obj = form.save()
            _audit_admin_change(
                request,
                "admin.course_section.updated",
                obj,
                f"Cập nhật lớp học phần {obj.code}.",
                {
                    "before": before,
                    "after": {
                        "code": obj.code,
                        "course_id": obj.course_id,
                        "term_id": obj.term_id,
                        "lecturer_id": obj.lecturer_id,
                        "max_students": obj.max_students,
                        "registration_open": obj.registration_open,
                        "is_active": obj.is_active,
                    },
                },
            )

        messages.success(request, "Đã cập nhật lớp học phần.")
        return redirect("admin_panel:course_section_list")

    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": f"Cập nhật lớp học phần: {obj.code}",
            "back_url": "admin_panel:course_section_list",
        },
    )


@admin_required
def admin_enrollment_list(request):
    query = request.GET.get("q", "").strip()[:100]
    section = request.GET.get("section", "").strip()
    status = request.GET.get("status", "").strip()

    queryset = get_enrollment_queryset(
        query=query,
        section=section,
        status=status,
    )

    return _admin_list(
        request,
        queryset,
        "admin_panel/enrollments/list.html",
        {
            "page_title": "Quản lý đăng ký học phần",
            "query": query,
            "selected_section": section,
            "selected_status": status,
            "sections": CourseSection.objects.select_related("course", "term").order_by("code"),
            "status_choices": EnrollmentStatus.choices,
        },
    )


@admin_required
@require_POST
def admin_enrollment_change_status(request, pk):
    new_status = request.POST.get("status", "").strip()

    try:
        with transaction.atomic():
            enrollment = Enrollment.objects.select_related(
                "student",
                "course_section",
            ).get(pk=pk)

            old_status = enrollment.status

            enrollment = change_enrollment_status(
                enrollment_id=enrollment.pk,
                new_status=new_status,
            )

            _audit_admin_change(
                request,
                "admin.enrollment.status_changed",
                enrollment,
                (
                    f"Thay đổi trạng thái đăng ký của "
                    f"{enrollment.student.student_code} "
                    f"tại lớp {enrollment.course_section.code}."
                ),
                {
                    "before": {"status": old_status},
                    "after": {"status": enrollment.status},
                },
            )

        messages.success(request, "Đã cập nhật trạng thái đăng ký.")

    except Enrollment.DoesNotExist:
        messages.error(request, "Không tìm thấy bản ghi đăng ký.")

    except ValidationError as exc:
        if hasattr(exc, "messages"):
            error_message = " ".join(exc.messages)
        else:
            error_message = str(exc)

        messages.error(request, error_message)

    return redirect("admin_panel:enrollment_list")


def _parse_admin_date(value):
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


@admin_required
def admin_classroom_list(request):
    query = request.GET.get("q", "").strip()[:100]
    building = request.GET.get("building", "").strip()[:100]
    classroom_type = request.GET.get("type", "").strip()
    active = request.GET.get("active", "").strip()

    queryset = get_classroom_queryset(
        query=query,
        building=building,
        classroom_type=classroom_type,
        active=active,
    )

    return _admin_list(
        request,
        queryset,
        "admin_panel/academic/list.html",
        {
            "page_title": "Quản lý phòng học",
            "create_url": "admin_panel:classroom_create",
            "edit_url": "admin_panel:classroom_update",
            "query": query,
            "selected_building": building,
            "selected_type": classroom_type,
            "selected_active": active,
            "classroom_types": ClassroomType.choices,
            "list_type": "classroom",
        },
    )


@admin_required
def admin_classroom_create(request):
    form = AdminClassroomForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            obj = form.save()
            _audit_admin_change(
                request,
                "admin.classroom.created",
                obj,
                f"Tạo phòng học {obj.code}.",
                {
                    "code": obj.code,
                    "name": obj.name,
                    "capacity": obj.capacity,
                },
            )

        messages.success(request, "Đã tạo phòng học.")
        return redirect("admin_panel:classroom_list")

    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": "Thêm phòng học",
            "back_url": "admin_panel:classroom_list",
        },
    )


@admin_required
def admin_classroom_update(request, pk):
    obj = get_object_or_404(Classroom, pk=pk)
    form = AdminClassroomForm(request.POST or None, instance=obj)

    if request.method == "POST" and form.is_valid():
        before = {
            "code": obj.code,
            "name": obj.name,
            "capacity": obj.capacity,
            "is_active": obj.is_active,
        }

        with transaction.atomic():
            obj = form.save()
            _audit_admin_change(
                request,
                "admin.classroom.updated",
                obj,
                f"Cập nhật phòng học {obj.code}.",
                {
                    "before": before,
                    "after": {
                        "code": obj.code,
                        "name": obj.name,
                        "capacity": obj.capacity,
                        "is_active": obj.is_active,
                    },
                },
            )

        messages.success(request, "Đã cập nhật phòng học.")
        return redirect("admin_panel:classroom_list")

    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": f"Cập nhật phòng học: {obj.code}",
            "back_url": "admin_panel:classroom_list",
        },
    )


@admin_required
@require_POST
def admin_classroom_toggle_active(request, pk):
    obj = get_object_or_404(Classroom, pk=pk)

    if obj.is_active and obj.timetables.filter(is_active=True).exists():
        messages.error(
            request,
            "Không thể ngừng hoạt động phòng đang được sử dụng trong thời khóa biểu.",
        )
        return redirect("admin_panel:classroom_list")

    obj.is_active = not obj.is_active
    obj.save(update_fields=["is_active", "updated_at"])

    _audit_admin_change(
        request,
        "admin.classroom.status_changed",
        obj,
        f"Thay đổi trạng thái phòng {obj.code}.",
        {"is_active": obj.is_active},
    )

    messages.success(request, "Đã cập nhật trạng thái phòng học.")
    return redirect("admin_panel:classroom_list")


@admin_required
def admin_timetable_list(request):
    query = request.GET.get("q", "").strip()[:100]
    term = request.GET.get("term", "").strip()
    course_section = request.GET.get("section", "").strip()
    classroom = request.GET.get("classroom", "").strip()
    weekday = request.GET.get("weekday", "").strip()
    active = request.GET.get("active", "").strip()

    queryset = get_timetable_queryset(
        query=query,
        term=term,
        course_section=course_section,
        classroom=classroom,
        weekday=weekday,
        active=active,
    )

    return _admin_list(
        request,
        queryset,
        "admin_panel/academic/list.html",
        {
            "page_title": "Quản lý thời khóa biểu",
            "create_url": "admin_panel:timetable_create",
            "edit_url": "admin_panel:timetable_update",
            "query": query,
            "selected_term": term,
            "selected_section": course_section,
            "selected_classroom": classroom,
            "selected_weekday": weekday,
            "selected_active": active,
            "terms": AcademicTerm.objects.order_by("-academic_year", "semester"),
            "sections": CourseSection.objects.select_related("course").order_by("code"),
            "classrooms": Classroom.objects.order_by("code"),
            "weekdays": Weekday.choices,
            "list_type": "timetable",
        },
    )


@admin_required
def admin_timetable_create(request):
    form = AdminTimetableForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            obj = form.save()
            _audit_admin_change(
                request,
                "admin.timetable.created",
                obj,
                f"Tạo thời khóa biểu cho {obj.course_section.code}.",
                {
                    "course_section_id": obj.course_section_id,
                    "classroom_id": obj.classroom_id,
                    "weekday": obj.weekday,
                },
            )

        messages.success(request, "Đã tạo thời khóa biểu.")
        return redirect("admin_panel:timetable_list")

    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": "Thêm thời khóa biểu",
            "back_url": "admin_panel:timetable_list",
        },
    )


@admin_required
def admin_timetable_update(request, pk):
    obj = get_object_or_404(Timetable, pk=pk)
    form = AdminTimetableForm(request.POST or None, instance=obj)

    if request.method == "POST" and form.is_valid():
        before = {
            "course_section_id": obj.course_section_id,
            "classroom_id": obj.classroom_id,
            "weekday": obj.weekday,
            "start_time": obj.start_time.isoformat(),
            "end_time": obj.end_time.isoformat(),
            "is_active": obj.is_active,
        }

        with transaction.atomic():
            obj = form.save()
            _audit_admin_change(
                request,
                "admin.timetable.updated",
                obj,
                f"Cập nhật thời khóa biểu {obj}.",
                {
                    "before": before,
                    "after": {
                        "course_section_id": obj.course_section_id,
                        "classroom_id": obj.classroom_id,
                        "weekday": obj.weekday,
                        "start_time": obj.start_time.isoformat(),
                        "end_time": obj.end_time.isoformat(),
                        "is_active": obj.is_active,
                    },
                },
            )

        messages.success(request, "Đã cập nhật thời khóa biểu.")
        return redirect("admin_panel:timetable_list")

    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": "Cập nhật thời khóa biểu",
            "back_url": "admin_panel:timetable_list",
        },
    )


@admin_required
def admin_class_session_list(request):
    query = request.GET.get("q", "").strip()[:100]
    term = request.GET.get("term", "").strip()
    timetable = request.GET.get("timetable", "").strip()
    classroom = request.GET.get("classroom", "").strip()
    status = request.GET.get("status", "").strip()
    date_from_raw = request.GET.get("date_from", "").strip()
    date_to_raw = request.GET.get("date_to", "").strip()

    date_from = _parse_admin_date(date_from_raw)
    date_to = _parse_admin_date(date_to_raw)

    if date_from_raw and date_from is None:
        messages.warning(request, "Ngày bắt đầu lọc không hợp lệ.")

    if date_to_raw and date_to is None:
        messages.warning(request, "Ngày kết thúc lọc không hợp lệ.")

    queryset = get_class_session_queryset(
        query=query,
        term=term,
        timetable=timetable,
        classroom=classroom,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )

    return _admin_list(
        request,
        queryset,
        "admin_panel/academic/list.html",
        {
            "page_title": "Quản lý buổi học",
            "create_url": "admin_panel:class_session_create",
            "edit_url": "admin_panel:class_session_update",
            "query": query,
            "selected_term": term,
            "selected_timetable": timetable,
            "selected_classroom": classroom,
            "selected_status": status,
            "date_from": date_from_raw if date_from else "",
            "date_to": date_to_raw if date_to else "",
            "terms": AcademicTerm.objects.order_by("-academic_year", "semester"),
            "timetables": Timetable.objects.select_related("course_section").order_by(
                "course_section__code"
            ),
            "classrooms": Classroom.objects.order_by("code"),
            "session_statuses": ClassSessionStatus.choices,
            "list_type": "class_session",
        },
    )


@admin_required
def admin_class_session_create(request):
    form = AdminClassSessionForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            obj = form.save()
            _audit_admin_change(
                request,
                "admin.class_session.created",
                obj,
                f"Tạo buổi học {obj}.",
                {
                    "timetable_id": obj.timetable_id,
                    "session_date": obj.session_date.isoformat(),
                    "status": obj.status,
                },
            )

        messages.success(request, "Đã tạo buổi học.")
        return redirect("admin_panel:class_session_list")

    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": "Thêm buổi học",
            "back_url": "admin_panel:class_session_list",
        },
    )


@admin_required
def admin_class_session_update(request, pk):
    obj = get_object_or_404(ClassSession, pk=pk)
    form = AdminClassSessionForm(request.POST or None, instance=obj)

    if request.method == "POST":
        # Phải lấy dữ liệu cũ TRƯỚC form.is_valid().
        before = {
            "timetable_id": obj.timetable_id,
            "session_date": obj.session_date.isoformat(),
            "status": obj.status,
            "topic": obj.topic,
            "note": obj.note,
        }

        if form.is_valid():
            with transaction.atomic():
                updated_obj = form.save()

                after = {
                    "timetable_id": updated_obj.timetable_id,
                    "session_date": updated_obj.session_date.isoformat(),
                    "status": updated_obj.status,
                    "topic": updated_obj.topic,
                    "note": updated_obj.note,
                }

                _audit_admin_change(
                    request,
                    "admin.class_session.updated",
                    updated_obj,
                    f"Cập nhật buổi học {updated_obj}.",
                    {
                        "before": before,
                        "after": after,
                    },
                )

            messages.success(request, "Đã cập nhật buổi học.")
            return redirect("admin_panel:class_session_list")

    return render(
        request,
        "admin_panel/academic/form.html",
        {
            "form": form,
            "page_title": f"Cập nhật buổi học: {obj}",
            "back_url": "admin_panel:class_session_list",
        },
    )


@admin_required
def admin_audit_log_list(request):
    query = request.GET.get("q", "").strip()[:100]
    action = request.GET.get("action", "").strip()[:100]
    object_type = request.GET.get("object_type", "").strip()[:100]

    queryset = get_audit_log_queryset(
        query=query,
        action=action,
        object_type=object_type,
    )

    object_types = AuditLog.objects.order_by().values_list("object_type", flat=True).distinct()

    actions = AuditLog.objects.order_by().values_list("action", flat=True).distinct()

    return _admin_list(
        request,
        queryset,
        "admin_panel/audit_logs/list.html",
        {
            "page_title": "Nhật ký hệ thống",
            "query": query,
            "selected_action": action,
            "selected_object_type": object_type,
            "object_types": object_types,
            "actions": actions,
        },
    )
