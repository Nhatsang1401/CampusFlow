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
