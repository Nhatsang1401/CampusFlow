from datetime import date, time

import pytest
from django.core.exceptions import ValidationError

from apps.academics.models import (
    AcademicTerm,
    Classroom,
    ClassroomType,
    ClassSession,
    ClassSessionStatus,
    Course,
    CourseSection,
    Faculty,
    LecturerProfile,
    Timetable,
    Weekday,
)
from apps.accounts.models import User, UserRole


@pytest.mark.django_db
class TestClassroom:
    def test_create_classroom(self):
        classroom = Classroom.objects.create(
            code="A101",
            name="Phòng A101",
            building="A",
            floor=1,
            capacity=50,
            classroom_type=ClassroomType.LECTURE,
        )

        assert classroom.pk is not None
        assert str(classroom) == "A101 - Phòng A101"

    def test_capacity_must_be_positive(self):
        classroom = Classroom(
            code="A102",
            name="Phòng A102",
            floor=1,
            capacity=0,
        )

        with pytest.raises(ValidationError):
            classroom.full_clean()

    def test_floor_must_be_positive(self):
        classroom = Classroom(
            code="A103",
            name="Phòng A103",
            floor=0,
            capacity=30,
        )

        with pytest.raises(ValidationError):
            classroom.full_clean()


@pytest.mark.django_db
class TestTimetable:
    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.faculty = Faculty.objects.create(
            code="CNTT",
            name="Công nghệ thông tin",
        )

        lecturer_user = User.objects.create_user(
            username="lecturer_day5",
            password="test-password",
            role=UserRole.LECTURER,
        )
        self.lecturer = LecturerProfile.objects.create(
            lecturer_code="GV001",
            user=lecturer_user,
            faculty=self.faculty,
        )

        self.course = Course.objects.create(
            code="IT101",
            name="Nhập môn Công nghệ thông tin",
            credits=3,
        )

        self.term = AcademicTerm.objects.create(
            code="HK1-2026",
            name="Học kỳ 1",
            academic_year="2026-2027",
            semester="1",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 1, 31),
        )

        self.section = CourseSection.objects.create(
            code="IT101-01",
            course=self.course,
            term=self.term,
            lecturer=self.lecturer,
            section_number=1,
            max_students=40,
        )

        self.classroom = Classroom.objects.create(
            code="A101",
            name="Phòng A101",
            building="A",
            floor=1,
            capacity=50,
        )

        self.timetable_data = {
            "course_section": self.section,
            "classroom": self.classroom,
            "weekday": Weekday.MONDAY,
            "start_time": time(7, 0),
            "end_time": time(9, 0),
            "effective_start": date(2026, 9, 1),
            "effective_end": date(2027, 1, 31),
        }

    def test_create_valid_timetable(self):
        timetable = Timetable(**self.timetable_data)
        timetable.full_clean()
        timetable.save()

        assert timetable.pk is not None

    def test_end_time_must_be_after_start_time(self):
        data = {
            **self.timetable_data,
            "start_time": time(9, 0),
            "end_time": time(9, 0),
        }

        with pytest.raises(ValidationError):
            Timetable(**data).full_clean()

    def test_effective_end_must_not_precede_start(self):
        data = {
            **self.timetable_data,
            "effective_start": date(2026, 10, 1),
            "effective_end": date(2026, 9, 1),
        }

        with pytest.raises(ValidationError):
            Timetable(**data).full_clean()

    def test_effective_dates_must_be_inside_term(self):
        data = {
            **self.timetable_data,
            "effective_start": date(2026, 8, 1),
        }

        with pytest.raises(ValidationError):
            Timetable(**data).full_clean()

    def test_classroom_capacity_must_cover_section(self):
        small_room = Classroom.objects.create(
            code="A102",
            name="Phòng nhỏ",
            floor=1,
            capacity=20,
        )
        data = {
            **self.timetable_data,
            "classroom": small_room,
        }

        with pytest.raises(ValidationError):
            Timetable(**data).full_clean()

    def test_inactive_classroom_cannot_be_scheduled(self):
        self.classroom.is_active = False
        self.classroom.save()

        with pytest.raises(ValidationError):
            Timetable(**self.timetable_data).full_clean()

    def test_same_room_cannot_have_overlapping_timetable(self):
        first = Timetable.objects.create(**self.timetable_data)

        second_data = {
            **self.timetable_data,
            "start_time": time(8, 0),
            "end_time": time(10, 0),
        }

        with pytest.raises(ValidationError):
            Timetable(**second_data).full_clean()

        assert Timetable.objects.filter(pk=first.pk).exists()

    def test_same_lecturer_cannot_teach_overlapping_classes(self):
        Timetable.objects.create(**self.timetable_data)

        another_course = Course.objects.create(
            code="IT102",
            name="Cơ sở lập trình",
            credits=3,
        )
        another_section = CourseSection.objects.create(
            code="IT102-01",
            course=another_course,
            term=self.term,
            lecturer=self.lecturer,
            section_number=1,
            max_students=30,
        )
        another_room = Classroom.objects.create(
            code="B101",
            name="Phòng B101",
            floor=1,
            capacity=40,
        )

        data = {
            **self.timetable_data,
            "course_section": another_section,
            "classroom": another_room,
            "start_time": time(8, 0),
            "end_time": time(10, 0),
        }

        with pytest.raises(ValidationError):
            Timetable(**data).full_clean()

    def test_different_rooms_and_lecturers_can_overlap(self):
        Timetable.objects.create(**self.timetable_data)

        another_lecturer_user = User.objects.create_user(
            username="lecturer_day5_2",
            password="test-password",
            role=UserRole.LECTURER,
        )
        another_lecturer = LecturerProfile.objects.create(
            lecturer_code="GV002",
            user=another_lecturer_user,
            faculty=self.faculty,
        )
        another_course = Course.objects.create(
            code="IT102",
            name="Cơ sở lập trình",
            credits=3,
        )
        another_section = CourseSection.objects.create(
            code="IT102-01",
            course=another_course,
            term=self.term,
            lecturer=another_lecturer,
            section_number=1,
            max_students=30,
        )
        another_room = Classroom.objects.create(
            code="B101",
            name="Phòng B101",
            floor=1,
            capacity=40,
        )

        data = {
            **self.timetable_data,
            "course_section": another_section,
            "classroom": another_room,
        }

        timetable = Timetable(**data)
        timetable.full_clean()
        timetable.save()

        assert Timetable.objects.count() == 2

    def test_adjacent_time_slots_do_not_conflict(self):
        Timetable.objects.create(**self.timetable_data)

        data = {
            **self.timetable_data,
            "start_time": time(9, 0),
            "end_time": time(11, 0),
        }

        timetable = Timetable(**data)
        timetable.full_clean()
        timetable.save()

        assert Timetable.objects.count() == 2

    def test_overlapping_effective_dates_conflict(self):
        Timetable.objects.create(**self.timetable_data)

        data = {
            **self.timetable_data,
            "effective_start": date(2026, 12, 1),
            "effective_end": date(2027, 1, 31),
        }

        # Khoảng ngày này vẫn giao với lịch cũ nên phải bị từ chối.
        with pytest.raises(ValidationError):
            Timetable(**data).full_clean()

    def test_inactive_timetable_does_not_block_new_schedule(self):
        Timetable.objects.create(
            **self.timetable_data,
            is_active=False,
        )

        timetable = Timetable(**self.timetable_data)
        timetable.full_clean()
        timetable.save()

        assert Timetable.objects.count() == 2


@pytest.mark.django_db
class TestClassSession:
    @pytest.fixture(autouse=True)
    def setup_data(self):
        faculty = Faculty.objects.create(
            code="KT",
            name="Kinh tế",
        )
        lecturer_user = User.objects.create_user(
            username="lecturer_session",
            password="test-password",
            role=UserRole.LECTURER,
        )
        lecturer = LecturerProfile.objects.create(
            lecturer_code="GV101",
            user=lecturer_user,
            faculty=faculty,
        )
        course = Course.objects.create(
            code="EC101",
            name="Kinh tế đại cương",
            credits=3,
        )
        term = AcademicTerm.objects.create(
            code="HK1-SESSION",
            name="Học kỳ 1",
            academic_year="2026-2027",
            semester="1",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 1, 31),
        )
        section = CourseSection.objects.create(
            code="EC101-01",
            course=course,
            term=term,
            lecturer=lecturer,
            section_number=1,
            max_students=30,
        )
        classroom = Classroom.objects.create(
            code="C101",
            name="Phòng C101",
            floor=1,
            capacity=40,
        )
        self.timetable = Timetable.objects.create(
            course_section=section,
            classroom=classroom,
            weekday=date(2026, 9, 7).weekday(),
            start_time=time(7, 0),
            end_time=time(9, 0),
            effective_start=date(2026, 9, 1),
            effective_end=date(2027, 1, 31),
        )

    def test_create_valid_session(self):
        session = ClassSession(
            timetable=self.timetable,
            session_date=date(2026, 9, 7),
        )
        session.full_clean()
        session.save()

        assert session.pk is not None
        assert session.status == ClassSessionStatus.UPCOMING

    def test_session_must_be_inside_timetable_period(self):
        session = ClassSession(
            timetable=self.timetable,
            session_date=date(2026, 8, 31),
        )

        with pytest.raises(ValidationError):
            session.full_clean()

    def test_session_must_be_on_correct_weekday(self):
        session = ClassSession(
            timetable=self.timetable,
            session_date=date(2026, 9, 8),
        )

        with pytest.raises(ValidationError):
            session.full_clean()

    def test_session_must_be_inside_academic_term(self):
        session = ClassSession(
            timetable=self.timetable,
            session_date=date(2026, 8, 31),
        )

        with pytest.raises(ValidationError):
            session.full_clean()

    def test_cancelled_session_can_be_saved(self):
        session = ClassSession(
            timetable=self.timetable,
            session_date=date(2026, 9, 7),
            status=ClassSessionStatus.CANCELLED,
        )
        session.full_clean()
        session.save()

        assert session.status == ClassSessionStatus.CANCELLED

    def test_duplicate_session_is_rejected(self):
        ClassSession.objects.create(
            timetable=self.timetable,
            session_date=date(2026, 9, 7),
        )

        duplicate = ClassSession(
            timetable=self.timetable,
            session_date=date(2026, 9, 7),
        )

        with pytest.raises(ValidationError):
            duplicate.validate_constraints()
