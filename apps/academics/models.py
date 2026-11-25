from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from apps.accounts.models import UserRole


class Gender(models.TextChoices):
    MALE = "male", "Nam"
    FEMALE = "female", "Nữ"
    OTHER = "other", "Khác"


class Semester(models.TextChoices):
    FIRST = "1", "Học kỳ 1"
    SECOND = "2", "Học kỳ 2"
    SUMMER = "summer", "Học kỳ hè"


class EnrollmentStatus(models.TextChoices):
    REGISTERED = "registered", "Đang đăng ký"
    CANCELLED = "cancelled", "Đã hủy"
    COMPLETED = "completed", "Đã hoàn thành"


class ClassroomType(models.TextChoices):
    LECTURE = "lecture", "Phòng lý thuyết"
    LAB = "lab", "Phòng thực hành"
    MEETING = "meeting", "Phòng hội thảo"
    OTHER = "other", "Khác"


class ClassSessionStatus(models.TextChoices):
    UPCOMING = "upcoming", "Sắp diễn ra"
    COMPLETED = "completed", "Đã hoàn thành"
    CANCELLED = "cancelled", "Đã hủy"


class Weekday(models.IntegerChoices):
    MONDAY = 0, "Thứ 2"
    TUESDAY = 1, "Thứ 3"
    WEDNESDAY = 2, "Thứ 4"
    THURSDAY = 3, "Thứ 5"
    FRIDAY = 4, "Thứ 6"
    SATURDAY = 5, "Thứ 7"
    SUNDAY = 6, "Chủ nhật"


class Faculty(models.Model):
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Mã khoa",
    )
    name = models.CharField(
        max_length=150,
        verbose_name="Tên khoa",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Mô tả",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Đang hoạt động",
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    class Meta:
        db_table = "academics_faculty"
        verbose_name = "Khoa"
        verbose_name_plural = "Danh sách khoa"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class AcademicClass(models.Model):
    code = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Mã lớp",
    )
    name = models.CharField(
        max_length=150,
        verbose_name="Tên lớp",
    )
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.PROTECT,
        related_name="classes",
        verbose_name="Khoa",
    )
    academic_year = models.CharField(
        max_length=9,
        verbose_name="Niên khóa",
        help_text="Ví dụ: 2024-2028",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Đang hoạt động",
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    class Meta:
        db_table = "academics_class"
        verbose_name = "Lớp hành chính"
        verbose_name_plural = "Danh sách lớp hành chính"
        ordering = ["code"]
        indexes = [
            models.Index(
                fields=["faculty", "is_active"],
                name="acad_class_fac_active_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class StudentProfile(models.Model):
    student_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Mã sinh viên",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="student_profile",
        verbose_name="Tài khoản",
    )
    academic_class = models.ForeignKey(
        AcademicClass,
        on_delete=models.PROTECT,
        related_name="students",
        verbose_name="Lớp hành chính",
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name="Ngày sinh",
    )
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True,
        default="",
        verbose_name="Giới tính",
    )
    address = models.TextField(
        blank=True,
        default="",
        verbose_name="Địa chỉ",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    class Meta:
        db_table = "academics_student_profile"
        verbose_name = "Hồ sơ sinh viên"
        verbose_name_plural = "Danh sách sinh viên"
        ordering = ["student_code"]
        indexes = [
            models.Index(
                fields=["academic_class", "student_code"],
                name="acad_student_class_code_idx",
            ),
        ]

    def clean(self):
        super().clean()

        if self.user_id:
            if self.user.is_superuser or self.user.role != UserRole.STUDENT:
                raise ValidationError({"user": ("Tài khoản được chọn phải có vai trò sinh viên.")})

    def __str__(self) -> str:
        return f"{self.student_code} - {self.user}"


class LecturerProfile(models.Model):
    lecturer_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Mã giảng viên",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="lecturer_profile",
        verbose_name="Tài khoản",
    )
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.PROTECT,
        related_name="lecturers",
        verbose_name="Khoa",
    )
    academic_title = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Học hàm / học vị",
    )
    office_room = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Phòng làm việc",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    class Meta:
        db_table = "academics_lecturer_profile"
        verbose_name = "Hồ sơ giảng viên"
        verbose_name_plural = "Danh sách giảng viên"
        ordering = ["lecturer_code"]
        indexes = [
            models.Index(
                fields=["faculty", "lecturer_code"],
                name="acad_lect_fac_code_idx",
            ),
        ]

    def clean(self):
        super().clean()

        if self.user_id:
            if self.user.is_superuser or self.user.role != UserRole.LECTURER:
                raise ValidationError({"user": ("Tài khoản được chọn phải có vai trò giảng viên.")})

    def __str__(self) -> str:
        return f"{self.lecturer_code} - {self.user}"


class Course(models.Model):
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Mã học phần",
    )
    name = models.CharField(
        max_length=200,
        verbose_name="Tên học phần",
    )
    credits = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10),
        ],
        verbose_name="Số tín chỉ",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Mô tả học phần",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Đang hoạt động",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    class Meta:
        db_table = "academics_course"
        verbose_name = "Học phần"
        verbose_name_plural = "Danh sách học phần"
        ordering = ["code"]
        constraints = [
            models.CheckConstraint(
                condition=Q(credits__gte=1) & Q(credits__lte=10),
                name="acad_course_credits_1_10",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class AcademicTerm(models.Model):
    code = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Mã học kỳ",
        help_text="Ví dụ: HK1-2026-2027",
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Tên học kỳ",
    )
    academic_year = models.CharField(
        max_length=9,
        verbose_name="Năm học",
        help_text="Ví dụ: 2026-2027",
    )
    semester = models.CharField(
        max_length=10,
        choices=Semester.choices,
        verbose_name="Học kỳ",
    )
    start_date = models.DateField(
        verbose_name="Ngày bắt đầu học kỳ",
    )
    end_date = models.DateField(
        verbose_name="Ngày kết thúc học kỳ",
    )
    registration_start = models.DateField(
        null=True,
        blank=True,
        verbose_name="Bắt đầu đăng ký",
    )
    registration_end = models.DateField(
        null=True,
        blank=True,
        verbose_name="Kết thúc đăng ký",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Đang hoạt động",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    class Meta:
        db_table = "academics_academic_term"
        verbose_name = "Học kỳ"
        verbose_name_plural = "Danh sách học kỳ"
        ordering = ["-academic_year", "semester"]
        constraints = [
            models.UniqueConstraint(
                fields=["academic_year", "semester"],
                name="acad_term_year_semester_uniq",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}

        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                errors["end_date"] = "Ngày kết thúc phải sau ngày bắt đầu."

        if self.registration_start and self.registration_end:
            if self.registration_start > self.registration_end:
                errors["registration_end"] = "Ngày kết thúc đăng ký phải sau ngày bắt đầu đăng ký."
        elif self.registration_start or self.registration_end:
            errors["registration_start"] = "Phải nhập đầy đủ cả ngày bắt đầu và kết thúc đăng ký."

        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class CourseSection(models.Model):
    code = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Mã lớp học phần",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="sections",
        verbose_name="Học phần",
    )
    term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.PROTECT,
        related_name="course_sections",
        verbose_name="Học kỳ",
    )
    lecturer = models.ForeignKey(
        LecturerProfile,
        on_delete=models.PROTECT,
        related_name="course_sections",
        verbose_name="Giảng viên phụ trách",
    )
    section_number = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Nhóm học phần",
    )
    max_students = models.PositiveSmallIntegerField(
        default=40,
        validators=[MinValueValidator(1)],
        verbose_name="Sĩ số tối đa",
    )
    registration_open = models.BooleanField(
        default=True,
        verbose_name="Cho phép đăng ký",
        db_index=True,
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Đang hoạt động",
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    class Meta:
        db_table = "academics_course_section"
        verbose_name = "Lớp học phần"
        verbose_name_plural = "Danh sách lớp học phần"
        ordering = ["term", "course", "section_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "term", "section_number"],
                name="acad_section_course_term_no_uniq",
            ),
            models.CheckConstraint(
                condition=Q(max_students__gte=1),
                name="acad_section_capacity_positive",
            ),
        ]
        indexes = [
            models.Index(
                fields=["term", "is_active"],
                name="acad_section_term_active_idx",
            ),
            models.Index(
                fields=["course", "term"],
                name="acad_section_course_term_idx",
            ),
        ]

    @property
    def enrolled_count(self) -> int:
        return self.enrollments.filter(status=EnrollmentStatus.REGISTERED).count()

    @property
    def available_seats(self) -> int:
        return max(0, self.max_students - self.enrolled_count)

    def clean(self):
        super().clean()
        errors = {}

        if self.max_students is not None and self.max_students < 1:
            errors["max_students"] = "Sĩ số tối đa phải lớn hơn 0."

        if self.pk and self.max_students is not None:
            current_count = self.enrollments.filter(status=EnrollmentStatus.REGISTERED).count()

            if self.max_students < current_count:
                errors["max_students"] = "Sĩ số tối đa không được nhỏ hơn số sinh viên đã đăng ký."

        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return f"{self.code} - {self.course.name}"


class Enrollment(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.PROTECT,
        related_name="enrollments",
        verbose_name="Sinh viên",
    )
    course_section = models.ForeignKey(
        CourseSection,
        on_delete=models.PROTECT,
        related_name="enrollments",
        verbose_name="Lớp học phần",
    )
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.REGISTERED,
        db_index=True,
        verbose_name="Trạng thái đăng ký",
    )
    registered_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày đăng ký",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    class Meta:
        db_table = "academics_enrollment"
        verbose_name = "Đăng ký học phần"
        verbose_name_plural = "Danh sách đăng ký học phần"
        ordering = ["-registered_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course_section"],
                name="acad_enroll_student_section_uniq",
            ),
        ]
        indexes = [
            models.Index(
                fields=["course_section", "status"],
                name="acad_enroll_section_status_idx",
            ),
            models.Index(
                fields=["student", "status"],
                name="acad_enroll_student_status_idx",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}

        if self.status == EnrollmentStatus.REGISTERED:
            if self.student_id and not self.student.user.is_active:
                errors["student"] = "Tài khoản sinh viên đã bị vô hiệu hóa."

            if self.course_section_id:
                section = self.course_section

                if not section.is_active:
                    errors["course_section"] = "Lớp học phần hiện không hoạt động."
                elif not section.registration_open:
                    errors["course_section"] = "Lớp học phần hiện không mở đăng ký."
                else:
                    current_count = (
                        Enrollment.objects.filter(
                            course_section=section,
                            status=EnrollmentStatus.REGISTERED,
                        )
                        .exclude(pk=self.pk)
                        .count()
                    )

                    if current_count >= section.max_students:
                        errors["course_section"] = "Lớp học phần đã đạt sĩ số tối đa."

        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return f"{self.student.student_code} - {self.course_section.code}"


class Classroom(models.Model):
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Mã phòng",
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Tên phòng",
    )
    building = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Tòa nhà",
    )
    floor = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Tầng",
    )
    capacity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Sức chứa",
    )
    classroom_type = models.CharField(
        max_length=20,
        choices=ClassroomType.choices,
        default=ClassroomType.LECTURE,
        verbose_name="Loại phòng",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Đang hoạt động",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Mô tả",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    class Meta:
        db_table = "academics_classroom"
        verbose_name = "Phòng học"
        verbose_name_plural = "Danh sách phòng học"
        ordering = ["building", "floor", "code"]
        constraints = [
            models.CheckConstraint(
                condition=Q(capacity__gte=1),
                name="acad_classroom_capacity_positive",
            ),
            models.CheckConstraint(
                condition=Q(floor__gte=1),
                name="acad_classroom_floor_positive",
            ),
        ]
        indexes = [
            models.Index(
                fields=["building", "floor"],
                name="acad_classroom_build_floor_idx",
            ),
            models.Index(
                fields=["is_active", "classroom_type"],
                name="acad_classroom_active_type_idx",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}

        if self.capacity is not None and self.capacity < 1:
            errors["capacity"] = "Sức chứa phòng phải lớn hơn 0."

        if self.floor is not None and self.floor < 1:
            errors["floor"] = "Tầng phải lớn hơn hoặc bằng 1."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Timetable(models.Model):
    course_section = models.ForeignKey(
        CourseSection,
        on_delete=models.PROTECT,
        related_name="timetables",
        verbose_name="Lớp học phần",
    )
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.PROTECT,
        related_name="timetables",
        verbose_name="Phòng học",
    )
    weekday = models.PositiveSmallIntegerField(
        choices=Weekday.choices,
        verbose_name="Thứ",
    )
    start_time = models.TimeField(
        verbose_name="Giờ bắt đầu",
    )
    end_time = models.TimeField(
        verbose_name="Giờ kết thúc",
    )
    effective_start = models.DateField(
        verbose_name="Ngày bắt đầu áp dụng",
    )
    effective_end = models.DateField(
        verbose_name="Ngày kết thúc áp dụng",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Đang áp dụng",
    )
    note = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Ghi chú",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    class Meta:
        db_table = "academics_timetable"
        verbose_name = "Thời khóa biểu"
        verbose_name_plural = "Danh sách thời khóa biểu"
        ordering = ["weekday", "start_time", "classroom"]
        indexes = [
            models.Index(
                fields=["weekday", "is_active"],
                name="acad_timetable_day_active_idx",
            ),
            models.Index(
                fields=["course_section", "is_active"],
                name="acad_tt_section_active_idx",
            ),
            models.Index(
                fields=["classroom", "weekday"],
                name="acad_timetable_room_day_idx",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}

        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                errors["end_time"] = "Giờ kết thúc phải sau giờ bắt đầu."

        if self.effective_start and self.effective_end:
            if self.effective_start > self.effective_end:
                errors["effective_end"] = "Ngày kết thúc áp dụng phải sau hoặc bằng ngày bắt đầu."

        if self.weekday not in Weekday.values:
            errors["weekday"] = "Thứ trong tuần không hợp lệ."

        if self.course_section_id and self.classroom_id:
            section = self.course_section
            classroom = self.classroom

            if not section.is_active:
                errors["course_section"] = "Lớp học phần không hoạt động."

            if not classroom.is_active:
                errors["classroom"] = "Phòng học hiện không hoạt động."

            if classroom.capacity < section.max_students:
                errors["classroom"] = "Sức chứa phòng không đủ cho sĩ số tối đa của lớp học phần."

            term = section.term
            if self.effective_start and self.effective_end:
                if self.effective_start < term.start_date or self.effective_end > term.end_date:
                    errors["effective_start"] = (
                        "Thời gian áp dụng phải nằm trong thời gian của học kỳ."
                    )

            if (
                self.is_active
                and self.start_time
                and self.end_time
                and self.effective_start
                and self.effective_end
                and self.weekday in Weekday.values
            ):
                conflicts = Timetable.objects.filter(
                    is_active=True,
                    weekday=self.weekday,
                    effective_start__lte=self.effective_end,
                    effective_end__gte=self.effective_start,
                    start_time__lt=self.end_time,
                    end_time__gt=self.start_time,
                ).filter(
                    Q(classroom_id=classroom.pk)
                    | Q(course_section__lecturer_id=section.lecturer_id)
                )

                if self.pk:
                    conflicts = conflicts.exclude(pk=self.pk)

                for conflict in conflicts.select_related(
                    "classroom",
                    "course_section__lecturer",
                ):
                    if conflict.classroom_id == classroom.pk:
                        errors["classroom"] = (
                            "Phòng học đã có lịch khác trong khoảng thời gian này."
                        )
                    if conflict.course_section.lecturer_id == section.lecturer_id:
                        errors["course_section"] = (
                            "Giảng viên đã có lịch dạy khác trong khoảng thời gian này."
                        )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.course_section.code} - "
            f"{self.get_weekday_display()} "
            f"{self.start_time:%H:%M}-{self.end_time:%H:%M}"
        )


class ClassSession(models.Model):
    timetable = models.ForeignKey(
        Timetable,
        on_delete=models.PROTECT,
        related_name="sessions",
        verbose_name="Lịch học",
    )
    session_date = models.DateField(
        verbose_name="Ngày học",
    )
    status = models.CharField(
        max_length=20,
        choices=ClassSessionStatus.choices,
        default=ClassSessionStatus.UPCOMING,
        db_index=True,
        verbose_name="Trạng thái buổi học",
    )
    topic = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Nội dung buổi học",
    )
    note = models.TextField(
        blank=True,
        default="",
        verbose_name="Ghi chú",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối",
    )

    class Meta:
        db_table = "academics_class_session"
        verbose_name = "Buổi học"
        verbose_name_plural = "Danh sách buổi học"
        ordering = ["session_date", "timetable__start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["timetable", "session_date"],
                name="acad_session_timetable_date_uniq",
            ),
        ]
        indexes = [
            models.Index(
                fields=["session_date", "status"],
                name="acad_session_date_status_idx",
            ),
            models.Index(
                fields=["timetable", "session_date"],
                name="acad_session_tt_date_idx",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}

        if self.timetable_id and self.session_date:
            timetable = self.timetable
            term = timetable.course_section.term

            if not timetable.is_active:
                errors["timetable"] = "Lịch học hiện không hoạt động."

            if not (timetable.effective_start <= self.session_date <= timetable.effective_end):
                errors["session_date"] = "Ngày học nằm ngoài thời gian áp dụng của thời khóa biểu."

            if not (term.start_date <= self.session_date <= term.end_date):
                errors["session_date"] = "Ngày học phải nằm trong thời gian của học kỳ."

            if self.session_date.weekday() != timetable.weekday:
                errors["session_date"] = "Ngày đã chọn không đúng thứ của thời khóa biểu."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.timetable.course_section.code} - {self.session_date:%d/%m/%Y}"
