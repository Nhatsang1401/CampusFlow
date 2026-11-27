import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.academics.models import (
    AcademicClass,
    Faculty,
    LecturerProfile,
    StudentProfile,
)
from apps.accounts.models import UserRole

User = get_user_model()


@pytest.fixture
def academic_admin_data(db):
    admin = User.objects.create_superuser(
        username="academic_admin",
        email="academic_admin@example.com",
        password="TestPassword123!",
    )
    faculty = Faculty.objects.create(
        code="CNTT",
        name="Công nghệ thông tin",
    )
    academic_class = AcademicClass.objects.create(
        code="CNTT-K65",
        name="Công nghệ thông tin K65",
        faculty=faculty,
        academic_year="2024-2028",
    )
    student_user = User.objects.create_user(
        username="academic_student",
        password="TestPassword123!",
        role=UserRole.STUDENT,
    )
    lecturer_user = User.objects.create_user(
        username="academic_lecturer",
        password="TestPassword123!",
        role=UserRole.LECTURER,
    )
    return {
        "admin": admin,
        "faculty": faculty,
        "class": academic_class,
        "student_user": student_user,
        "lecturer_user": lecturer_user,
    }


@pytest.mark.django_db
class TestAcademicManagementAccess:
    @pytest.mark.parametrize(
        "url_name",
        [
            "faculty_list",
            "class_list",
            "student_list",
            "lecturer_list",
        ],
    )
    def test_anonymous_user_redirected(self, client, url_name):
        response = client.get(reverse(f"admin_panel:{url_name}"))
        assert response.status_code == 302
        assert reverse("accounts:login") in response.url

    @pytest.mark.parametrize(
        "url_name",
        [
            "faculty_list",
            "class_list",
            "student_list",
            "lecturer_list",
        ],
    )
    def test_student_cannot_access(self, client, academic_admin_data, url_name):
        client.force_login(academic_admin_data["student_user"])
        response = client.get(reverse(f"admin_panel:{url_name}"))
        assert response.status_code == 302

    @pytest.mark.parametrize(
        "url_name",
        [
            "faculty_list",
            "class_list",
            "student_list",
            "lecturer_list",
        ],
    )
    def test_admin_can_access(self, client, academic_admin_data, url_name):
        client.force_login(academic_admin_data["admin"])
        response = client.get(reverse(f"admin_panel:{url_name}"))
        assert response.status_code == 200


@pytest.mark.django_db
class TestFacultyManagement:
    def test_create_faculty(self, client, academic_admin_data):
        client.force_login(academic_admin_data["admin"])
        response = client.post(
            reverse("admin_panel:faculty_create"),
            {
                "code": "DIEN",
                "name": "Điện - Điện tử",
                "description": "Khoa điện",
                "is_active": "on",
            },
        )
        assert response.status_code == 302
        assert Faculty.objects.filter(code="DIEN").exists()

    def test_duplicate_faculty_code_rejected(self, client, academic_admin_data):
        client.force_login(academic_admin_data["admin"])
        response = client.post(
            reverse("admin_panel:faculty_create"),
            {
                "code": "CNTT",
                "name": "Khoa trùng mã",
                "is_active": "on",
            },
        )
        assert response.status_code == 200
        assert Faculty.objects.count() == 1

    def test_update_faculty(self, client, academic_admin_data):
        client.force_login(academic_admin_data["admin"])
        faculty = academic_admin_data["faculty"]
        response = client.post(
            reverse("admin_panel:faculty_update", args=[faculty.pk]),
            {
                "code": faculty.code,
                "name": "Công nghệ thông tin và truyền thông",
                "description": "",
                "is_active": "on",
            },
        )
        assert response.status_code == 302
        faculty.refresh_from_db()
        assert faculty.name == "Công nghệ thông tin và truyền thông"


@pytest.mark.django_db
class TestAcademicClassManagement:
    def test_create_class(self, client, academic_admin_data):
        client.force_login(academic_admin_data["admin"])
        response = client.post(
            reverse("admin_panel:class_create"),
            {
                "code": "CNTT-K66",
                "name": "Công nghệ thông tin K66",
                "faculty": academic_admin_data["faculty"].pk,
                "academic_year": "2025-2029",
                "is_active": "on",
            },
        )
        assert response.status_code == 302
        assert AcademicClass.objects.filter(code="CNTT-K66").exists()

    def test_filter_classes_by_faculty(self, client, academic_admin_data):
        client.force_login(academic_admin_data["admin"])
        response = client.get(
            reverse("admin_panel:class_list"),
            {"faculty": academic_admin_data["faculty"].pk},
        )
        assert response.status_code == 200
        assert response.context["page_obj"].paginator.count == 1


@pytest.mark.django_db
class TestProfileManagement:
    def test_create_student_profile(self, client, academic_admin_data):
        client.force_login(academic_admin_data["admin"])
        response = client.post(
            reverse("admin_panel:student_create"),
            {
                "student_code": "SV001",
                "user": academic_admin_data["student_user"].pk,
                "academic_class": academic_admin_data["class"].pk,
                "date_of_birth": "2005-01-01",
                "gender": "male",
                "address": "Hà Nội",
            },
        )
        assert response.status_code == 302
        assert StudentProfile.objects.filter(student_code="SV001").exists()

    def test_student_profile_rejects_lecturer_account(self, client, academic_admin_data):
        client.force_login(academic_admin_data["admin"])
        response = client.post(
            reverse("admin_panel:student_create"),
            {
                "student_code": "SV002",
                "user": academic_admin_data["lecturer_user"].pk,
                "academic_class": academic_admin_data["class"].pk,
                "gender": "male",
            },
        )
        assert response.status_code == 200
        assert not StudentProfile.objects.filter(student_code="SV002").exists()

    def test_create_lecturer_profile(self, client, academic_admin_data):
        client.force_login(academic_admin_data["admin"])
        response = client.post(
            reverse("admin_panel:lecturer_create"),
            {
                "lecturer_code": "GV001",
                "user": academic_admin_data["lecturer_user"].pk,
                "faculty": academic_admin_data["faculty"].pk,
                "academic_title": "Thạc sĩ",
                "office_room": "A101",
            },
        )
        assert response.status_code == 302
        assert LecturerProfile.objects.filter(lecturer_code="GV001").exists()

    def test_lecturer_profile_rejects_student_account(self, client, academic_admin_data):
        client.force_login(academic_admin_data["admin"])
        response = client.post(
            reverse("admin_panel:lecturer_create"),
            {
                "lecturer_code": "GV002",
                "user": academic_admin_data["student_user"].pk,
                "faculty": academic_admin_data["faculty"].pk,
            },
        )
        assert response.status_code == 200
        assert not LecturerProfile.objects.filter(lecturer_code="GV002").exists()


@pytest.mark.django_db
class TestAcademicStatus:
    def test_faculty_status_toggle_requires_post(self, client, academic_admin_data):
        client.force_login(academic_admin_data["admin"])
        faculty = academic_admin_data["faculty"]
        url = reverse(
            "admin_panel:academic_toggle_status",
            args=["faculty", faculty.pk],
        )
        response = client.get(url)
        assert response.status_code == 405
        faculty.refresh_from_db()
        assert faculty.is_active is True

    def test_faculty_can_be_deactivated(self, client, academic_admin_data):
        client.force_login(academic_admin_data["admin"])
        faculty = academic_admin_data["faculty"]
        response = client.post(
            reverse(
                "admin_panel:academic_toggle_status",
                args=["faculty", faculty.pk],
            )
        )
        assert response.status_code == 302
        faculty.refresh_from_db()
        assert faculty.is_active is False
