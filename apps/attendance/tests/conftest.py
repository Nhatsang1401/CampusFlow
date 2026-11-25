from datetime import date, time

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.academics.models import (
    AcademicClass,
    AcademicTerm,
    Classroom,
    ClassSession,
    Course,
    CourseSection,
    Enrollment,
    Faculty,
    LecturerProfile,
    StudentProfile,
    Timetable,
    Weekday,
)
from apps.accounts.models import UserRole

User = get_user_model()


@pytest.fixture
def attendance_data(db):
    faculty = Faculty.objects.create(
        code="CNTT",
        name="Công nghệ thông tin",
    )

    academic_class = AcademicClass.objects.create(
        code="CNTT-K20",
        name="Công nghệ thông tin K20",
        faculty=faculty,
        academic_year="2024-2028",
    )

    lecturer_user = User.objects.create_user(
        username="lecturer_test",
        password="TestPassword123!",
        role=UserRole.LECTURER,
    )

    LecturerProfile.objects.create(
        user=lecturer_user,
        lecturer_code="GV001",
        faculty=faculty,
    )

    other_lecturer = User.objects.create_user(
        username="lecturer_other",
        password="TestPassword123!",
        role=UserRole.LECTURER,
    )

    LecturerProfile.objects.create(
        user=other_lecturer,
        lecturer_code="GV002",
        faculty=faculty,
    )

    student_user = User.objects.create_user(
        username="student_test",
        password="TestPassword123!",
        role=UserRole.STUDENT,
    )

    student_profile = StudentProfile.objects.create(
        student_code="SV001",
        user=student_user,
        academic_class=academic_class,
    )

    course = Course.objects.create(
        code="IT101",
        name="Lập trình Python",
        credits=3,
    )

    term = AcademicTerm.objects.create(
        code="HK1-2026",
        name="Học kỳ 1 năm 2026",
        academic_year="2026-2027",
        semester=1,
        start_date=date(2026, 9, 1),
        end_date=date(2027, 1, 31),
    )

    section = CourseSection.objects.create(
        code="IT101-01",
        course=course,
        term=term,
        lecturer=lecturer_user.lecturer_profile,
        section_number=1,
        max_students=50,
        registration_open=True,
        is_active=True,
    )

    enrollment = Enrollment.objects.create(
        student=student_profile,
        course_section=section,
    )

    classroom = Classroom.objects.create(
        code="A101",
        name="Phòng A101",
        building="A",
        floor=1,
        capacity=60,
        is_active=True,
    )

    timetable = Timetable.objects.create(
        course_section=section,
        classroom=classroom,
        weekday=Weekday.MONDAY,
        start_time=time(7, 0),
        end_time=time(9, 0),
        effective_start=date(2026, 9, 1),
        effective_end=date(2027, 1, 31),
    )

    class_session = ClassSession.objects.create(
        timetable=timetable,
        session_date=date(2026, 9, 7),
    )

    return {
        "faculty": faculty,
        "lecturer_user": lecturer_user,
        "other_lecturer": other_lecturer,
        "student_user": student_user,
        "course": course,
        "term": term,
        "section": section,
        "classroom": classroom,
        "timetable": timetable,
        "class_session": class_session,
        "academic_class": academic_class,
        "student_profile": student_profile,
        "enrollment": enrollment,
    }


@pytest.fixture
def api_client():
    return APIClient()
