from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.academics.models import (
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

User = get_user_model()


class CourseModelTests(TestCase):
    def setUp(self):
        self.faculty = Faculty.objects.create(
            code="CNTT",
            name="Công nghệ thông tin",
        )

        self.academic_class = self.faculty.classes.create(
            code="CNTT-K65",
            name="Công nghệ thông tin K65",
            academic_year="2024-2028",
        )

        self.student_user = User.objects.create_user(
            username="student_day4",
            password="CampusFlowTest!2026",
            role=UserRole.STUDENT,
        )

        self.student = StudentProfile.objects.create(
            student_code="SV-DAY4-001",
            user=self.student_user,
            academic_class=self.academic_class,
        )

        self.lecturer_user = User.objects.create_user(
            username="lecturer_day4",
            password="CampusFlowTest!2026",
            role=UserRole.LECTURER,
        )

        self.lecturer = LecturerProfile.objects.create(
            lecturer_code="GV-DAY4-001",
            user=self.lecturer_user,
            faculty=self.faculty,
        )

        self.course = Course.objects.create(
            code="IT101",
            name="Nhập môn Công nghệ thông tin",
            credits=3,
        )

        self.term = AcademicTerm.objects.create(
            code="HK1-2026-2027",
            name="Học kỳ 1 năm học 2026-2027",
            academic_year="2026-2027",
            semester=Semester.FIRST,
            start_date=date(2026, 9, 1),
            end_date=date(2027, 1, 15),
            registration_start=date(2026, 8, 1),
            registration_end=date(2026, 8, 25),
        )

        self.section = CourseSection.objects.create(
            code="IT101-01",
            course=self.course,
            term=self.term,
            lecturer=self.lecturer,
            section_number=1,
            max_students=2,
            registration_open=True,
        )

    def test_create_course(self):
        self.assertEqual(self.course.code, "IT101")
        self.assertEqual(self.course.credits, 3)
        self.assertEqual(
            str(self.course),
            "IT101 - Nhập môn Công nghệ thông tin",
        )

    def test_course_rejects_invalid_credit_count(self):
        course = Course(
            code="IT102",
            name="Học phần không hợp lệ",
            credits=11,
        )

        with self.assertRaises(ValidationError):
            course.full_clean()

    def test_create_academic_term(self):
        self.assertEqual(self.term.semester, Semester.FIRST)
        self.assertEqual(self.term.academic_year, "2026-2027")

    def test_academic_term_rejects_invalid_date_range(self):
        term = AcademicTerm(
            code="HK-INVALID",
            name="Học kỳ không hợp lệ",
            academic_year="2027-2028",
            semester=Semester.SECOND,
            start_date=date(2027, 12, 1),
            end_date=date(2027, 9, 1),
        )

        with self.assertRaises(ValidationError):
            term.full_clean()

    def test_academic_term_rejects_invalid_registration_range(self):
        term = AcademicTerm(
            code="HK-INVALID-REG",
            name="Học kỳ đăng ký sai",
            academic_year="2027-2028",
            semester=Semester.SECOND,
            start_date=date(2027, 9, 1),
            end_date=date(2028, 1, 15),
            registration_start=date(2027, 8, 20),
            registration_end=date(2027, 8, 10),
        )

        with self.assertRaises(ValidationError):
            term.full_clean()

    def test_create_course_section(self):
        self.assertEqual(self.section.course, self.course)
        self.assertEqual(self.section.term, self.term)
        self.assertEqual(self.section.lecturer, self.lecturer)
        self.assertEqual(self.section.enrolled_count, 0)
        self.assertEqual(self.section.available_seats, 2)

    def test_course_section_rejects_duplicate_section_number(self):
        section = CourseSection(
            code="IT101-01-DUP",
            course=self.course,
            term=self.term,
            lecturer=self.lecturer,
            section_number=1,
            max_students=30,
        )

        with self.assertRaises(ValidationError):
            section.full_clean()

    def test_course_section_rejects_invalid_capacity(self):
        section = CourseSection(
            code="IT101-INVALID",
            course=self.course,
            term=self.term,
            lecturer=self.lecturer,
            section_number=2,
            max_students=0,
        )

        with self.assertRaises(ValidationError):
            section.full_clean()

    def test_create_enrollment(self):
        enrollment = Enrollment.objects.create(
            student=self.student,
            course_section=self.section,
        )

        self.assertEqual(enrollment.status, EnrollmentStatus.REGISTERED)
        self.assertEqual(self.section.enrolled_count, 1)
        self.assertEqual(self.section.available_seats, 1)

    def test_enrollment_rejects_closed_registration(self):
        self.section.registration_open = False
        self.section.save()

        enrollment = Enrollment(
            student=self.student,
            course_section=self.section,
        )

        with self.assertRaises(ValidationError):
            enrollment.full_clean()

    def test_enrollment_rejects_inactive_section(self):
        self.section.is_active = False
        self.section.save()

        enrollment = Enrollment(
            student=self.student,
            course_section=self.section,
        )

        with self.assertRaises(ValidationError):
            enrollment.full_clean()

    def test_enrollment_rejects_inactive_student(self):
        self.student_user.is_active = False
        self.student_user.save()

        enrollment = Enrollment(
            student=self.student,
            course_section=self.section,
        )

        with self.assertRaises(ValidationError):
            enrollment.full_clean()

    def test_enrollment_rejects_full_section(self):
        other_user = User.objects.create_user(
            username="student_day4_02",
            password="CampusFlowTest!2026",
            role=UserRole.STUDENT,
        )

        other_student = StudentProfile.objects.create(
            student_code="SV-DAY4-002",
            user=other_user,
            academic_class=self.academic_class,
        )

        Enrollment.objects.create(
            student=other_student,
            course_section=self.section,
        )

        Enrollment.objects.create(
            student=self.student,
            course_section=self.section,
        )

        third_user = User.objects.create_user(
            username="student_day4_03",
            password="CampusFlowTest!2026",
            role=UserRole.STUDENT,
        )

        third_student = StudentProfile.objects.create(
            student_code="SV-DAY4-003",
            user=third_user,
            academic_class=self.academic_class,
        )

        enrollment = Enrollment(
            student=third_student,
            course_section=self.section,
        )

        with self.assertRaises(ValidationError):
            enrollment.full_clean()

    def test_database_rejects_duplicate_enrollment(self):
        Enrollment.objects.create(
            student=self.student,
            course_section=self.section,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Enrollment.objects.create(
                    student=self.student,
                    course_section=self.section,
                )

    def test_cancelled_enrollment_does_not_count_towards_capacity(self):
        enrollment = Enrollment.objects.create(
            student=self.student,
            course_section=self.section,
        )

        enrollment.status = EnrollmentStatus.CANCELLED
        enrollment.save()

        self.assertEqual(self.section.enrolled_count, 0)
        self.assertEqual(self.section.available_seats, 2)

    def test_course_cannot_be_deleted_when_section_exists(self):
        with self.assertRaises(ProtectedError):
            self.course.delete()

    def test_term_cannot_be_deleted_when_section_exists(self):
        with self.assertRaises(ProtectedError):
            self.term.delete()

    def test_lecturer_cannot_be_deleted_when_section_exists(self):
        with self.assertRaises(ProtectedError):
            self.lecturer.delete()

    def test_section_cannot_be_deleted_when_enrollment_exists(self):
        Enrollment.objects.create(
            student=self.student,
            course_section=self.section,
        )

        with self.assertRaises(ProtectedError):
            self.section.delete()

    def test_section_capacity_cannot_be_lowered_below_enrollment_count(self):
        second_user = User.objects.create_user(
            username="student_capacity_02",
            password="CampusFlowTest!2026",
            role=UserRole.STUDENT,
        )
        second_student = StudentProfile.objects.create(
            student_code="SV-CAPACITY-002",
            user=second_user,
            academic_class=self.academic_class,
        )

        Enrollment.objects.create(
            student=self.student,
            course_section=self.section,
        )
        Enrollment.objects.create(
            student=second_student,
            course_section=self.section,
        )

        self.section.max_students = 1

        with self.assertRaises(ValidationError):
            self.section.full_clean()
