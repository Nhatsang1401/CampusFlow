from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.academics.models import (
    AcademicClass,
    Faculty,
    Gender,
    LecturerProfile,
    StudentProfile,
)
from apps.accounts.models import UserRole

User = get_user_model()


class AcademicModelTests(TestCase):
    def setUp(self):
        self.faculty = Faculty.objects.create(
            code="CNTT",
            name="Công nghệ thông tin",
        )
        self.academic_class = AcademicClass.objects.create(
            code="CNTT-K65",
            name="Công nghệ thông tin K65",
            faculty=self.faculty,
            academic_year="2024-2028",
        )

    def create_user(self, username, role):
        return User.objects.create_user(
            username=username,
            password="CampusFlowTest!2026",
            role=role,
        )

    def test_create_faculty(self):
        self.assertEqual(self.faculty.code, "CNTT")
        self.assertEqual(str(self.faculty), "CNTT - Công nghệ thông tin")

    def test_create_academic_class(self):
        self.assertEqual(self.academic_class.faculty, self.faculty)
        self.assertEqual(
            str(self.academic_class),
            "CNTT-K65 - Công nghệ thông tin K65",
        )

    def test_create_student_profile(self):
        user = self.create_user("student01", UserRole.STUDENT)

        student = StudentProfile.objects.create(
            student_code="SV0001",
            user=user,
            academic_class=self.academic_class,
            date_of_birth=date(2005, 5, 10),
            gender=Gender.MALE,
        )

        self.assertEqual(student.user, user)
        self.assertEqual(student.academic_class, self.academic_class)
        self.assertEqual(user.student_profile, student)

    def test_student_profile_rejects_lecturer_account(self):
        lecturer = self.create_user("lecturer01", UserRole.LECTURER)

        student = StudentProfile(
            student_code="SV0002",
            user=lecturer,
            academic_class=self.academic_class,
        )

        with self.assertRaises(ValidationError):
            student.full_clean()

    def test_student_profile_rejects_superuser(self):
        admin = User.objects.create_superuser(
            username="admin_test",
            email="admin@example.com",
            password="CampusFlowAdmin!2026",
        )

        student = StudentProfile(
            student_code="SV0003",
            user=admin,
            academic_class=self.academic_class,
        )

        with self.assertRaises(ValidationError):
            student.full_clean()

    def test_create_lecturer_profile(self):
        user = self.create_user("lecturer02", UserRole.LECTURER)

        lecturer = LecturerProfile.objects.create(
            lecturer_code="GV0001",
            user=user,
            faculty=self.faculty,
            academic_title="Thạc sĩ",
            office_room="A301",
        )

        self.assertEqual(lecturer.faculty, self.faculty)
        self.assertEqual(user.lecturer_profile, lecturer)

    def test_lecturer_profile_rejects_student_account(self):
        student = self.create_user("student02", UserRole.STUDENT)

        lecturer = LecturerProfile(
            lecturer_code="GV0002",
            user=student,
            faculty=self.faculty,
        )

        with self.assertRaises(ValidationError):
            lecturer.full_clean()

    def test_lecturer_profile_rejects_superuser(self):
        admin = User.objects.create_superuser(
            username="admin_lecturer_test",
            email="admin2@example.com",
            password="CampusFlowAdmin!2026",
        )

        lecturer = LecturerProfile(
            lecturer_code="GV0003",
            user=admin,
            faculty=self.faculty,
        )

        with self.assertRaises(ValidationError):
            lecturer.full_clean()

    def test_faculty_cannot_be_deleted_when_class_exists(self):
        with self.assertRaises(ProtectedError):
            self.faculty.delete()

    def test_class_cannot_be_deleted_when_student_exists(self):
        user = self.create_user("student03", UserRole.STUDENT)

        StudentProfile.objects.create(
            student_code="SV0004",
            user=user,
            academic_class=self.academic_class,
        )

        with self.assertRaises(ProtectedError):
            self.academic_class.delete()

    def test_user_cannot_be_deleted_when_student_profile_exists(self):
        user = self.create_user("student04", UserRole.STUDENT)

        StudentProfile.objects.create(
            student_code="SV0005",
            user=user,
            academic_class=self.academic_class,
        )

        with self.assertRaises(ProtectedError):
            user.delete()
