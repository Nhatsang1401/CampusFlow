import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.academics.models import (
    AcademicClass,
    AcademicTerm,
    Course,
    CourseSection,
    Enrollment,
    EnrollmentStatus,
    Faculty,
    LecturerProfile,
    Semester,
    StudentProfile,
)
from apps.accounts.models import UserRole
from apps.dashboards.admin_forms import AdminCourseSectionForm
from apps.dashboards.admin_services import (
    change_enrollment_status,
    get_course_section_queryset,
    get_enrollment_queryset,
)

User = get_user_model()


@pytest.fixture
def course_admin(db):
    return User.objects.create_superuser(
        username="section_admin",
        email="section_admin@example.com",
        password="TestPassword123!",
    )


@pytest.fixture
def course_data(db):
    faculty = Faculty.objects.create(
        code="CNTT",
        name="Công nghệ thông tin",
    )
    academic_class = AcademicClass.objects.create(
        code="CNTT2024A",
        name="Công nghệ thông tin 2024 A",
        faculty=faculty,
        academic_year="2024-2028",
    )

    lecturer_user = User.objects.create_user(
        username="section_lecturer",
        password="TestPassword123!",
        role=UserRole.LECTURER,
    )
    lecturer = LecturerProfile.objects.create(
        lecturer_code="GV001",
        user=lecturer_user,
        faculty=faculty,
    )

    student_user = User.objects.create_user(
        username="section_student",
        password="TestPassword123!",
        role=UserRole.STUDENT,
    )
    student = StudentProfile.objects.create(
        student_code="SV001",
        user=student_user,
        academic_class=academic_class,
    )

    another_student_user = User.objects.create_user(
        username="section_student2",
        password="TestPassword123!",
        role=UserRole.STUDENT,
    )
    another_student = StudentProfile.objects.create(
        student_code="SV002",
        user=another_student_user,
        academic_class=academic_class,
    )

    term = AcademicTerm.objects.create(
        code="HK1-2026-2027",
        name="Học kỳ 1 năm học 2026-2027",
        academic_year="2026-2027",
        semester=Semester.FIRST,
        start_date="2026-09-01",
        end_date="2027-01-15",
        registration_start="2026-08-01",
        registration_end="2026-08-31",
    )

    course = Course.objects.create(
        code="CS101",
        name="Nhập môn lập trình",
        credits=3,
    )

    section = CourseSection.objects.create(
        code="CS101-HK1-01",
        course=course,
        term=term,
        lecturer=lecturer,
        section_number=1,
        max_students=2,
        registration_open=True,
        is_active=True,
    )

    return {
        "faculty": faculty,
        "academic_class": academic_class,
        "lecturer_user": lecturer_user,
        "lecturer": lecturer,
        "student_user": student_user,
        "student": student,
        "another_student_user": another_student_user,
        "another_student": another_student,
        "term": term,
        "course": course,
        "section": section,
    }


@pytest.fixture
def registered_enrollment(course_data):
    return Enrollment.objects.create(
        student=course_data["student"],
        course_section=course_data["section"],
        status=EnrollmentStatus.REGISTERED,
    )


@pytest.fixture
def cancelled_enrollment(course_data):
    return Enrollment.objects.create(
        student=course_data["student"],
        course_section=course_data["section"],
        status=EnrollmentStatus.CANCELLED,
    )


@pytest.mark.django_db
class TestAdminCourseSectionForm:
    def test_valid_course_section_form(self, course_data):
        form = AdminCourseSectionForm(
            data={
                "code": "CS101-HK1-02",
                "course": course_data["course"].pk,
                "term": course_data["term"].pk,
                "lecturer": course_data["lecturer"].pk,
                "section_number": 2,
                "max_students": 40,
                "registration_open": True,
                "is_active": True,
            }
        )

        assert form.is_valid(), form.errors

    def test_form_rejects_duplicate_section_number(self, course_data):
        form = AdminCourseSectionForm(
            data={
                "code": "CS101-HK1-DUP",
                "course": course_data["course"].pk,
                "term": course_data["term"].pk,
                "lecturer": course_data["lecturer"].pk,
                "section_number": 1,
                "max_students": 40,
                "registration_open": True,
                "is_active": True,
            }
        )

        assert not form.is_valid()

    def test_form_rejects_duplicate_section_code(self, course_data):
        form = AdminCourseSectionForm(
            data={
                "code": course_data["section"].code,
                "course": course_data["course"].pk,
                "term": course_data["term"].pk,
                "lecturer": course_data["lecturer"].pk,
                "section_number": 2,
                "max_students": 40,
                "registration_open": True,
                "is_active": True,
            }
        )

        assert not form.is_valid()

    def test_form_rejects_zero_capacity(self, course_data):
        form = AdminCourseSectionForm(
            data={
                "code": "CS101-HK1-03",
                "course": course_data["course"].pk,
                "term": course_data["term"].pk,
                "lecturer": course_data["lecturer"].pk,
                "section_number": 3,
                "max_students": 0,
                "registration_open": True,
                "is_active": True,
            }
        )

        assert not form.is_valid()

    def test_form_rejects_capacity_below_current_enrollment(
        self,
        course_data,
        registered_enrollment,
    ):
        Enrollment.objects.create(
            student=course_data["another_student"],
            course_section=course_data["section"],
            status=EnrollmentStatus.REGISTERED,
        )

        form = AdminCourseSectionForm(
            data={
                "code": course_data["section"].code,
                "course": course_data["course"].pk,
                "term": course_data["term"].pk,
                "lecturer": course_data["lecturer"].pk,
                "section_number": 1,
                "max_students": 1,
                "registration_open": True,
                "is_active": True,
            },
            instance=course_data["section"],
        )

        assert not form.is_valid()
        assert "max_students" in form.errors


@pytest.mark.django_db
class TestAdminCourseSectionQueryset:
    def test_search_by_section_code(self, course_data):
        queryset = get_course_section_queryset(query="CS101-HK1-01")

        assert queryset.filter(pk=course_data["section"].pk).exists()

    def test_filter_by_term(self, course_data):
        queryset = get_course_section_queryset(term=str(course_data["term"].pk))

        assert queryset.filter(pk=course_data["section"].pk).exists()

    def test_filter_by_course(self, course_data):
        queryset = get_course_section_queryset(course=str(course_data["course"].pk))

        assert queryset.filter(pk=course_data["section"].pk).exists()

    def test_filter_by_lecturer(self, course_data):
        queryset = get_course_section_queryset(lecturer=str(course_data["lecturer"].pk))

        assert queryset.filter(pk=course_data["section"].pk).exists()

    def test_filter_inactive_sections(self, course_data):
        course_data["section"].is_active = False
        course_data["section"].save(update_fields=["is_active"])

        queryset = get_course_section_queryset(active="inactive")

        assert queryset.filter(pk=course_data["section"].pk).exists()


@pytest.mark.django_db
class TestAdminEnrollmentQueryset:
    def test_search_by_student_code(self, course_data, registered_enrollment):
        queryset = get_enrollment_queryset(query="SV001")

        assert queryset.filter(pk=registered_enrollment.pk).exists()

    def test_filter_by_course_section(self, course_data, registered_enrollment):
        queryset = get_enrollment_queryset(section=str(course_data["section"].pk))

        assert queryset.filter(pk=registered_enrollment.pk).exists()

    def test_filter_by_status(self, registered_enrollment):
        queryset = get_enrollment_queryset(status=EnrollmentStatus.REGISTERED)

        assert queryset.filter(pk=registered_enrollment.pk).exists()

    def test_invalid_status_does_not_apply_status_filter(
        self,
        registered_enrollment,
    ):
        queryset = get_enrollment_queryset(status="invalid-status")

        assert queryset.filter(pk=registered_enrollment.pk).exists()


@pytest.mark.django_db
class TestChangeEnrollmentStatus:
    def test_registered_can_be_cancelled(self, registered_enrollment):
        enrollment = change_enrollment_status(
            enrollment_id=registered_enrollment.pk,
            new_status=EnrollmentStatus.CANCELLED,
        )

        assert enrollment.status == EnrollmentStatus.CANCELLED

    def test_registered_can_be_completed(self, registered_enrollment):
        enrollment = change_enrollment_status(
            enrollment_id=registered_enrollment.pk,
            new_status=EnrollmentStatus.COMPLETED,
        )

        assert enrollment.status == EnrollmentStatus.COMPLETED

    def test_cancelled_can_be_registered_again(self, cancelled_enrollment):
        enrollment = change_enrollment_status(
            enrollment_id=cancelled_enrollment.pk,
            new_status=EnrollmentStatus.REGISTERED,
        )

        assert enrollment.status == EnrollmentStatus.REGISTERED

    def test_same_status_is_idempotent(self, registered_enrollment):
        enrollment = change_enrollment_status(
            enrollment_id=registered_enrollment.pk,
            new_status=EnrollmentStatus.REGISTERED,
        )

        assert enrollment.status == EnrollmentStatus.REGISTERED

    def test_completed_enrollment_cannot_be_reactivated(
        self,
        course_data,
    ):
        enrollment = Enrollment.objects.create(
            student=course_data["student"],
            course_section=course_data["section"],
            status=EnrollmentStatus.COMPLETED,
        )

        with pytest.raises(ValidationError):
            change_enrollment_status(
                enrollment_id=enrollment.pk,
                new_status=EnrollmentStatus.REGISTERED,
            )

    def test_invalid_status_is_rejected(self, registered_enrollment):
        with pytest.raises(ValidationError):
            change_enrollment_status(
                enrollment_id=registered_enrollment.pk,
                new_status="unknown",
            )

    def test_cancelled_enrollment_cannot_be_reactivated_when_section_is_full(
        self,
        course_data,
        cancelled_enrollment,
    ):
        course_data["section"].max_students = 1
        course_data["section"].save(update_fields=["max_students"])

        Enrollment.objects.create(
            student=course_data["another_student"],
            course_section=course_data["section"],
            status=EnrollmentStatus.REGISTERED,
        )

        with pytest.raises(ValidationError):
            change_enrollment_status(
                enrollment_id=cancelled_enrollment.pk,
                new_status=EnrollmentStatus.REGISTERED,
            )

        cancelled_enrollment.refresh_from_db()
        assert cancelled_enrollment.status == EnrollmentStatus.CANCELLED

    def test_cancelled_enrollment_cannot_be_reactivated_when_registration_closed(
        self,
        course_data,
        cancelled_enrollment,
    ):
        course_data["section"].registration_open = False
        course_data["section"].save(update_fields=["registration_open"])

        with pytest.raises(ValidationError):
            change_enrollment_status(
                enrollment_id=cancelled_enrollment.pk,
                new_status=EnrollmentStatus.REGISTERED,
            )

    def test_cancelled_enrollment_cannot_be_reactivated_when_section_inactive(
        self,
        course_data,
        cancelled_enrollment,
    ):
        course_data["section"].is_active = False
        course_data["section"].save(update_fields=["is_active"])

        with pytest.raises(ValidationError):
            change_enrollment_status(
                enrollment_id=cancelled_enrollment.pk,
                new_status=EnrollmentStatus.REGISTERED,
            )

    def test_cancelled_enrollment_cannot_be_reactivated_for_inactive_student(
        self,
        course_data,
        cancelled_enrollment,
    ):
        course_data["student_user"].is_active = False
        course_data["student_user"].save(update_fields=["is_active"])

        with pytest.raises(ValidationError):
            change_enrollment_status(
                enrollment_id=cancelled_enrollment.pk,
                new_status=EnrollmentStatus.REGISTERED,
            )
