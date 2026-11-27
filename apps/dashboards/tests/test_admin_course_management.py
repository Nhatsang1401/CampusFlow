import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.academics.models import AcademicTerm, Course
from apps.accounts.models import UserRole

User = get_user_model()


@pytest.fixture
def course_admin(db):
    return User.objects.create_superuser(
        username="course_admin",
        email="course_admin@example.com",
        password="TestPassword123!",
    )


@pytest.fixture
def course_client(client, course_admin):
    client.force_login(course_admin)
    return client


@pytest.mark.django_db
class TestAdminTermManagement:
    def test_admin_can_open_term_list(self, course_client):
        response = course_client.get(reverse("admin_panel:term_list"))
        assert response.status_code == 200

    def test_admin_can_create_term(self, course_client):
        response = course_client.post(
            reverse("admin_panel:term_create"),
            {
                "code": "HK1-2026-2027",
                "name": "Học kỳ 1 năm học 2026-2027",
                "academic_year": "2026-2027",
                "semester": "1",
                "start_date": "2026-09-01",
                "end_date": "2027-01-15",
                "registration_start": "2026-08-01",
                "registration_end": "2026-08-25",
                "is_active": "on",
            },
        )

        assert response.status_code == 302
        assert AcademicTerm.objects.filter(code="HK1-2026-2027").exists()

    def test_term_rejects_invalid_date_range(self, course_client):
        response = course_client.post(
            reverse("admin_panel:term_create"),
            {
                "code": "INVALID-TERM",
                "name": "Học kỳ lỗi",
                "academic_year": "2026-2027",
                "semester": "1",
                "start_date": "2027-01-15",
                "end_date": "2026-09-01",
                "is_active": "on",
            },
        )

        assert response.status_code == 200
        assert not AcademicTerm.objects.filter(code="INVALID-TERM").exists()

    def test_duplicate_term_code_is_rejected(self, course_client):
        AcademicTerm.objects.create(
            code="HK1-2026-2027",
            name="Học kỳ 1",
            academic_year="2026-2027",
            semester="1",
            start_date="2026-09-01",
            end_date="2027-01-15",
        )

        response = course_client.post(
            reverse("admin_panel:term_create"),
            {
                "code": "HK1-2026-2027",
                "name": "Học kỳ trùng",
                "academic_year": "2027-2028",
                "semester": "1",
                "start_date": "2027-09-01",
                "end_date": "2028-01-15",
                "is_active": "on",
            },
        )

        assert response.status_code == 200
        assert AcademicTerm.objects.count() == 1


@pytest.mark.django_db
class TestAdminCourseManagement:
    def test_admin_can_open_course_list(self, course_client):
        response = course_client.get(reverse("admin_panel:course_list"))
        assert response.status_code == 200

    def test_admin_can_create_course(self, course_client):
        response = course_client.post(
            reverse("admin_panel:course_create"),
            {
                "code": "IT101",
                "name": "Nhập môn Công nghệ thông tin",
                "credits": 3,
                "description": "Học phần cơ sở.",
                "is_active": "on",
            },
        )

        assert response.status_code == 302
        assert Course.objects.filter(code="IT101").exists()

    def test_course_rejects_invalid_credits(self, course_client):
        response = course_client.post(
            reverse("admin_panel:course_create"),
            {
                "code": "IT999",
                "name": "Học phần không hợp lệ",
                "credits": 11,
                "description": "",
                "is_active": "on",
            },
        )

        assert response.status_code == 200
        assert not Course.objects.filter(code="IT999").exists()

    def test_duplicate_course_code_is_rejected(self, course_client):
        Course.objects.create(
            code="IT101",
            name="Nhập môn CNTT",
            credits=3,
        )

        response = course_client.post(
            reverse("admin_panel:course_create"),
            {
                "code": "IT101",
                "name": "Học phần trùng",
                "credits": 2,
                "is_active": "on",
            },
        )

        assert response.status_code == 200
        assert Course.objects.count() == 1

    def test_student_cannot_access_course_management(self, client, db):
        student = User.objects.create_user(
            username="course_student",
            password="TestPassword123!",
            role=UserRole.STUDENT,
        )
        client.force_login(student)

        response = client.get(reverse("admin_panel:course_list"))

        assert response.status_code == 302
