from datetime import date, time

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.academics.models import (
    AcademicClass,
    AcademicTerm,
    Classroom,
    ClassroomType,
    ClassSession,
    ClassSessionStatus,
    Course,
    CourseSection,
    Faculty,
    LecturerProfile,
    Semester,
    StudentProfile,
    Timetable,
    Weekday,
)
from apps.accounts.models import UserRole
from apps.dashboards.admin_services import (
    get_class_session_queryset,
    get_classroom_queryset,
    get_timetable_queryset,
)

User = get_user_model()


@pytest.fixture
def schedule_admin(db):
    return User.objects.create_superuser(
        username="schedule_admin",
        email="schedule_admin@example.com",
        password="TestPassword123!",
    )


@pytest.fixture
def schedule_client(client, schedule_admin):
    client.force_login(schedule_admin)
    return client


@pytest.fixture
def schedule_data(db):
    faculty = Faculty.objects.create(
        code="CNTT-SCH",
        name="Công nghệ thông tin",
    )

    academic_class = AcademicClass.objects.create(
        code="CNTT2024-SCH",
        name="Công nghệ thông tin 2024",
        faculty=faculty,
        academic_year="2024-2028",
    )

    lecturer_user = User.objects.create_user(
        username="schedule_lecturer",
        password="TestPassword123!",
        role=UserRole.LECTURER,
    )
    lecturer = LecturerProfile.objects.create(
        lecturer_code="GV-SCH-01",
        user=lecturer_user,
        faculty=faculty,
    )

    student_user = User.objects.create_user(
        username="schedule_student",
        password="TestPassword123!",
        role=UserRole.STUDENT,
    )
    student = StudentProfile.objects.create(
        student_code="SV-SCH-01",
        user=student_user,
        academic_class=academic_class,
    )

    term = AcademicTerm.objects.create(
        code="HK1-SCH-2026",
        name="Học kỳ kiểm thử",
        academic_year="2026-2027",
        semester=Semester.FIRST,
        start_date=date(2026, 9, 1),
        end_date=date(2027, 1, 15),
        registration_start=date(2026, 8, 1),
        registration_end=date(2026, 8, 31),
    )

    course = Course.objects.create(
        code="SCH101",
        name="Kiểm thử hệ thống",
        credits=3,
    )

    section = CourseSection.objects.create(
        code="SCH101-HK1-01",
        course=course,
        term=term,
        lecturer=lecturer,
        section_number=1,
        max_students=2,
        registration_open=True,
        is_active=True,
    )

    classroom = Classroom.objects.create(
        code="A-SCH-101",
        name="Phòng kiểm thử",
        building="A",
        floor=1,
        capacity=40,
        classroom_type=ClassroomType.LECTURE,
        is_active=True,
    )

    timetable = Timetable.objects.create(
        course_section=section,
        classroom=classroom,
        weekday=Weekday.TUESDAY,
        start_time=time(8, 0),
        end_time=time(10, 0),
        effective_start=date(2026, 9, 1),
        effective_end=date(2027, 1, 15),
        is_active=True,
    )

    class_session = ClassSession.objects.create(
        timetable=timetable,
        session_date=date(2026, 9, 8),
        status=ClassSessionStatus.UPCOMING,
        topic="Buổi học kiểm thử",
        note="Ghi chú ban đầu",
    )

    return {
        "faculty": faculty,
        "academic_class": academic_class,
        "lecturer": lecturer,
        "student": student,
        "term": term,
        "course": course,
        "section": section,
        "classroom": classroom,
        "timetable": timetable,
        "class_session": class_session,
    }


@pytest.mark.django_db
class TestAdminScheduleAccess:
    def test_admin_can_open_classroom_list(self, schedule_client):
        response = schedule_client.get(reverse("admin_panel:classroom_list"))
        assert response.status_code == 200

    def test_admin_can_open_timetable_list(self, schedule_client):
        response = schedule_client.get(reverse("admin_panel:timetable_list"))
        assert response.status_code == 200

    def test_admin_can_open_class_session_list(self, schedule_client):
        response = schedule_client.get(reverse("admin_panel:class_session_list"))
        assert response.status_code == 200

    def test_student_cannot_open_schedule_management(self, client, db):
        student = User.objects.create_user(
            username="schedule_forbidden_student",
            password="TestPassword123!",
            role=UserRole.STUDENT,
        )
        client.force_login(student)

        response = client.get(reverse("admin_panel:classroom_list"))

        assert response.status_code == 302


@pytest.mark.django_db
class TestClassroomManagement:
    def test_admin_can_create_classroom(self, schedule_client):
        response = schedule_client.post(
            reverse("admin_panel:classroom_create"),
            {
                "code": "B-SCH-201",
                "name": "Phòng học B201",
                "building": "B",
                "floor": 2,
                "capacity": 50,
                "classroom_type": ClassroomType.LECTURE,
                "is_active": "on",
                "description": "Phòng học mới",
            },
        )

        assert response.status_code == 302
        assert Classroom.objects.filter(code="B-SCH-201").exists()

    def test_classroom_rejects_zero_capacity(self, schedule_client):
        response = schedule_client.post(
            reverse("admin_panel:classroom_create"),
            {
                "code": "B-SCH-INVALID",
                "name": "Phòng không hợp lệ",
                "building": "B",
                "floor": 2,
                "capacity": 0,
                "classroom_type": ClassroomType.LECTURE,
                "is_active": "on",
                "description": "",
            },
        )

        assert response.status_code == 200
        assert not Classroom.objects.filter(code="B-SCH-INVALID").exists()

    def test_classroom_filter_by_building(self, schedule_data):
        queryset = get_classroom_queryset(building="A")

        assert queryset.filter(pk=schedule_data["classroom"].pk).exists()

    def test_classroom_filter_by_type(self, schedule_data):
        queryset = get_classroom_queryset(
            classroom_type=ClassroomType.LECTURE,
        )

        assert queryset.filter(pk=schedule_data["classroom"].pk).exists()

    def test_cannot_deactivate_classroom_with_active_timetable(
        self,
        schedule_client,
        schedule_data,
    ):
        response = schedule_client.post(
            reverse(
                "admin_panel:classroom_toggle_active",
                args=[schedule_data["classroom"].pk],
            )
        )

        assert response.status_code == 302

        schedule_data["classroom"].refresh_from_db()
        assert schedule_data["classroom"].is_active is True

    def test_inactive_classroom_can_be_activated(
        self,
        schedule_client,
        schedule_data,
    ):
        classroom = schedule_data["classroom"]
        classroom.is_active = False
        classroom.save(update_fields=["is_active"])

        response = schedule_client.post(
            reverse("admin_panel:classroom_toggle_active", args=[classroom.pk])
        )

        assert response.status_code == 302

        classroom.refresh_from_db()
        assert classroom.is_active is True

    def test_classroom_toggle_rejects_get(
        self,
        schedule_client,
        schedule_data,
    ):
        response = schedule_client.get(
            reverse(
                "admin_panel:classroom_toggle_active",
                args=[schedule_data["classroom"].pk],
            )
        )

        assert response.status_code == 405


@pytest.mark.django_db
class TestTimetableManagement:
    def test_timetable_filter_by_term(self, schedule_data):
        queryset = get_timetable_queryset(term=str(schedule_data["term"].pk))

        assert queryset.filter(pk=schedule_data["timetable"].pk).exists()

    def test_timetable_filter_by_section(self, schedule_data):
        queryset = get_timetable_queryset(
            course_section=str(schedule_data["section"].pk),
        )

        assert queryset.filter(pk=schedule_data["timetable"].pk).exists()

    def test_timetable_filter_by_classroom(self, schedule_data):
        queryset = get_timetable_queryset(
            classroom=str(schedule_data["classroom"].pk),
        )

        assert queryset.filter(pk=schedule_data["timetable"].pk).exists()

    def test_timetable_filter_by_weekday(self, schedule_data):
        queryset = get_timetable_queryset(
            weekday=str(Weekday.TUESDAY),
        )

        assert queryset.filter(pk=schedule_data["timetable"].pk).exists()

    def test_admin_can_create_timetable(self, schedule_client, schedule_data):
        second_classroom = Classroom.objects.create(
            code="B-SCH-202",
            name="Phòng học B202",
            building="B",
            floor=2,
            capacity=40,
            classroom_type=ClassroomType.LECTURE,
            is_active=True,
        )

        response = schedule_client.post(
            reverse("admin_panel:timetable_create"),
            {
                "course_section": schedule_data["section"].pk,
                "classroom": second_classroom.pk,
                "weekday": Weekday.TUESDAY,
                "start_time": "13:00",
                "end_time": "15:00",
                "effective_start": "2026-09-01",
                "effective_end": "2027-01-15",
                "is_active": "on",
                "note": "Lịch buổi chiều",
            },
        )

        assert response.status_code == 302
        assert Timetable.objects.filter(
            course_section=schedule_data["section"],
            classroom=second_classroom,
            start_time=time(13, 0),
        ).exists()


@pytest.mark.django_db
class TestClassSessionManagement:
    def test_class_session_filter_by_term(self, schedule_data):
        queryset = get_class_session_queryset(
            term=str(schedule_data["term"].pk),
        )

        assert queryset.filter(pk=schedule_data["class_session"].pk).exists()

    def test_class_session_filter_by_timetable(self, schedule_data):
        queryset = get_class_session_queryset(
            timetable=str(schedule_data["timetable"].pk),
        )

        assert queryset.filter(pk=schedule_data["class_session"].pk).exists()

    def test_class_session_filter_by_classroom(self, schedule_data):
        queryset = get_class_session_queryset(
            classroom=str(schedule_data["classroom"].pk),
        )

        assert queryset.filter(pk=schedule_data["class_session"].pk).exists()

    def test_class_session_filter_by_status(self, schedule_data):
        queryset = get_class_session_queryset(
            status=ClassSessionStatus.UPCOMING,
        )

        assert queryset.filter(pk=schedule_data["class_session"].pk).exists()

    def test_class_session_filter_by_date_range(self, schedule_data):
        queryset = get_class_session_queryset(
            date_from=date(2026, 9, 1),
            date_to=date(2026, 9, 30),
        )

        assert queryset.filter(pk=schedule_data["class_session"].pk).exists()

    def test_admin_can_create_class_session(self, schedule_client, schedule_data):
        response = schedule_client.post(
            reverse("admin_panel:class_session_create"),
            {
                "timetable": schedule_data["timetable"].pk,
                "session_date": "2026-09-15",
                "status": ClassSessionStatus.UPCOMING,
                "topic": "Buổi học thứ hai",
                "note": "Ghi chú thứ hai",
            },
        )

        assert response.status_code == 302
        assert ClassSession.objects.filter(
            timetable=schedule_data["timetable"],
            session_date=date(2026, 9, 15),
        ).exists()

    def test_class_session_rejects_wrong_weekday(
        self,
        schedule_client,
        schedule_data,
    ):
        response = schedule_client.post(
            reverse("admin_panel:class_session_create"),
            {
                "timetable": schedule_data["timetable"].pk,
                "session_date": "2026-09-09",
                "status": ClassSessionStatus.UPCOMING,
                "topic": "Sai thứ",
                "note": "",
            },
        )

        assert response.status_code == 200
        assert not ClassSession.objects.filter(
            timetable=schedule_data["timetable"],
            session_date=date(2026, 9, 9),
        ).exists()

    def test_duplicate_class_session_date_is_rejected(
        self,
        schedule_client,
        schedule_data,
    ):
        response = schedule_client.post(
            reverse("admin_panel:class_session_create"),
            {
                "timetable": schedule_data["timetable"].pk,
                "session_date": "2026-09-08",
                "status": ClassSessionStatus.UPCOMING,
                "topic": "Buổi trùng",
                "note": "",
            },
        )

        assert response.status_code == 200
        assert (
            ClassSession.objects.filter(
                timetable=schedule_data["timetable"],
                session_date=date(2026, 9, 8),
            ).count()
            == 1
        )

    def test_update_writes_topic_and_note_to_audit_log(
        self,
        schedule_client,
        schedule_data,
    ):
        from apps.core.models import AuditLog

        class_session = schedule_data["class_session"]

        response = schedule_client.post(
            reverse(
                "admin_panel:class_session_update",
                args=[class_session.pk],
            ),
            {
                "timetable": schedule_data["timetable"].pk,
                "session_date": "2026-09-08",
                "status": ClassSessionStatus.UPCOMING,
                "topic": "Nội dung đã cập nhật",
                "note": "Ghi chú đã cập nhật",
            },
        )

        assert response.status_code == 302

        log = AuditLog.objects.filter(
            action="admin.class_session.updated",
            object_id=str(class_session.pk),
        ).latest("created_at")

        assert log.changes["before"]["topic"] == "Buổi học kiểm thử"
        assert log.changes["before"]["note"] == "Ghi chú ban đầu"
        assert log.changes["after"]["topic"] == "Nội dung đã cập nhật"
        assert log.changes["after"]["note"] == "Ghi chú đã cập nhật"
