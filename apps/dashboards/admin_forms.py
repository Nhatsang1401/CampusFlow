from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.academics.models import (
    AcademicClass,
    AcademicTerm,
    Classroom,
    ClassSession,
    ClassSessionStatus,
    Course,
    CourseSection,
    Faculty,
    LecturerProfile,
    StudentProfile,
    Timetable,
)
from apps.accounts.models import UserRole
from apps.attendance.models import AttendanceSession, AttendanceSessionStatus

User = get_user_model()


class AdminUserCreateForm(forms.ModelForm):
    password = forms.CharField(
        label="Mật khẩu",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        min_length=10,
    )
    password_confirm = forms.CharField(
        label="Xác nhận mật khẩu",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "role",
            "is_active",
            "is_staff",
        )
        labels = {
            "username": "Tên đăng nhập",
            "first_name": "Tên",
            "last_name": "Họ",
            "email": "Email",
            "phone_number": "Số điện thoại",
            "role": "Vai trò",
            "is_active": "Tài khoản hoạt động",
            "is_staff": "Được truy cập Django Admin",
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("password_confirm")
        if password and confirm and password != confirm:
            self.add_error("password_confirm", "Mật khẩu xác nhận không khớp.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            self.save_m2m()
        return user


class AdminUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "role",
            "is_active",
            "is_staff",
        )
        labels = {
            "username": "Tên đăng nhập",
            "first_name": "Tên",
            "last_name": "Họ",
            "email": "Email",
            "phone_number": "Số điện thoại",
            "role": "Vai trò",
            "is_active": "Tài khoản hoạt động",
            "is_staff": "Được truy cập Django Admin",
        }

    def clean_role(self):
        role = self.cleaned_data["role"]
        if role not in UserRole.values:
            raise forms.ValidationError("Vai trò tài khoản không hợp lệ.")
        return role


class AdminFacultyForm(forms.ModelForm):
    class Meta:
        model = Faculty
        fields = ("code", "name", "description", "is_active")
        labels = {
            "code": "Mã khoa",
            "name": "Tên khoa",
            "description": "Mô tả",
            "is_active": "Đang hoạt động",
        }
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class AdminAcademicClassForm(forms.ModelForm):
    class Meta:
        model = AcademicClass
        fields = ("code", "name", "faculty", "academic_year", "is_active")
        labels = {
            "code": "Mã lớp",
            "name": "Tên lớp",
            "faculty": "Khoa",
            "academic_year": "Niên khóa",
            "is_active": "Đang hoạt động",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["faculty"].queryset = Faculty.objects.filter(is_active=True)
        if self.instance.pk and not self.instance.faculty.is_active:
            self.fields["faculty"].queryset = (
                Faculty.objects.filter(pk=self.instance.faculty_id)
                | self.fields["faculty"].queryset
            )


class AdminStudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = (
            "student_code",
            "user",
            "academic_class",
            "date_of_birth",
            "gender",
            "address",
        )
        labels = {
            "student_code": "Mã sinh viên",
            "user": "Tài khoản sinh viên",
            "academic_class": "Lớp hành chính",
            "date_of_birth": "Ngày sinh",
            "gender": "Giới tính",
            "address": "Địa chỉ",
        }
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        users = User.objects.filter(
            role=UserRole.STUDENT,
            is_superuser=False,
        ).order_by("username")
        if self.instance.pk:
            users = users.filter(Q(pk=self.instance.user_id) | Q(student_profile__isnull=True))
        else:
            users = users.filter(student_profile__isnull=True)
        self.fields["user"].queryset = users
        self.fields["academic_class"].queryset = AcademicClass.objects.filter(is_active=True)


class AdminLecturerProfileForm(forms.ModelForm):
    class Meta:
        model = LecturerProfile
        fields = (
            "lecturer_code",
            "user",
            "faculty",
            "academic_title",
            "office_room",
        )
        labels = {
            "lecturer_code": "Mã giảng viên",
            "user": "Tài khoản giảng viên",
            "faculty": "Khoa",
            "academic_title": "Học hàm / học vị",
            "office_room": "Phòng làm việc",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        users = User.objects.filter(
            role=UserRole.LECTURER,
            is_superuser=False,
        ).order_by("username")
        if self.instance.pk:
            users = users.filter(pk=self.instance.user_id)
        else:
            users = users.exclude(lecturer_profile__isnull=False)
        self.fields["user"].queryset = users
        self.fields["faculty"].queryset = Faculty.objects.filter(is_active=True)

    def models_q_user_profile(user_id):
        from django.db.models import Q

        return Q(pk=user_id)


class AdminAcademicTermForm(forms.ModelForm):
    class Meta:
        model = AcademicTerm
        fields = (
            "code",
            "name",
            "academic_year",
            "semester",
            "start_date",
            "end_date",
            "registration_start",
            "registration_end",
            "is_active",
        )
        labels = {
            "code": "Mã học kỳ",
            "name": "Tên học kỳ",
            "academic_year": "Năm học",
            "semester": "Học kỳ",
            "start_date": "Ngày bắt đầu",
            "end_date": "Ngày kết thúc",
            "registration_start": "Bắt đầu đăng ký",
            "registration_end": "Kết thúc đăng ký",
            "is_active": "Đang hoạt động",
        }
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "registration_start": forms.DateInput(attrs={"type": "date"}),
            "registration_end": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()

        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")
        registration_start = cleaned_data.get("registration_start")
        registration_end = cleaned_data.get("registration_end")

        if start and end and start > end:
            self.add_error("end_date", "Ngày kết thúc phải sau ngày bắt đầu.")

        if registration_start and registration_end:
            if registration_start > registration_end:
                self.add_error(
                    "registration_end",
                    "Ngày kết thúc đăng ký phải sau ngày bắt đầu đăng ký.",
                )
        elif registration_start or registration_end:
            self.add_error(
                "registration_end",
                "Phải nhập đầy đủ cả ngày bắt đầu và kết thúc đăng ký.",
            )

        return cleaned_data


class AdminCourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = (
            "code",
            "name",
            "credits",
            "description",
            "is_active",
        )
        labels = {
            "code": "Mã học phần",
            "name": "Tên học phần",
            "credits": "Số tín chỉ",
            "description": "Mô tả học phần",
            "is_active": "Đang hoạt động",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_credits(self):
        credits = self.cleaned_data["credits"]
        if not 1 <= credits <= 10:
            raise forms.ValidationError("Số tín chỉ phải từ 1 đến 10.")
        return credits


class AdminCourseSectionForm(forms.ModelForm):
    class Meta:
        model = CourseSection
        fields = (
            "code",
            "course",
            "term",
            "lecturer",
            "section_number",
            "max_students",
            "registration_open",
            "is_active",
        )
        labels = {
            "code": "Mã lớp học phần",
            "course": "Học phần",
            "term": "Học kỳ",
            "lecturer": "Giảng viên phụ trách",
            "section_number": "Nhóm học phần",
            "max_students": "Sĩ số tối đa",
            "registration_open": "Cho phép đăng ký",
            "is_active": "Đang hoạt động",
        }
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "course": forms.Select(attrs={"class": "form-control"}),
            "term": forms.Select(attrs={"class": "form-control"}),
            "lecturer": forms.Select(attrs={"class": "form-control"}),
            "section_number": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "max_students": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "registration_open": forms.CheckboxInput(),
            "is_active": forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Giữ cả các đối tượng đã ngừng hoạt động để không làm mất
        # lựa chọn hiện tại khi Admin chỉnh sửa dữ liệu cũ.
        self.fields["course"].queryset = Course.objects.order_by("code")
        self.fields["term"].queryset = AcademicTerm.objects.order_by("-academic_year", "semester")
        self.fields["lecturer"].queryset = LecturerProfile.objects.select_related(
            "user", "faculty"
        ).order_by("lecturer_code")


class AdminClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = (
            "code",
            "name",
            "building",
            "floor",
            "capacity",
            "classroom_type",
            "is_active",
            "description",
        )
        labels = {
            "code": "Mã phòng",
            "name": "Tên phòng",
            "building": "Tòa nhà",
            "floor": "Tầng",
            "capacity": "Sức chứa",
            "classroom_type": "Loại phòng",
            "is_active": "Đang hoạt động",
            "description": "Mô tả",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "floor": forms.NumberInput(attrs={"min": 1}),
            "capacity": forms.NumberInput(attrs={"min": 1}),
        }


class AdminTimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        fields = (
            "course_section",
            "classroom",
            "weekday",
            "start_time",
            "end_time",
            "effective_start",
            "effective_end",
            "is_active",
            "note",
        )
        labels = {
            "course_section": "Lớp học phần",
            "classroom": "Phòng học",
            "weekday": "Thứ",
            "start_time": "Giờ bắt đầu",
            "end_time": "Giờ kết thúc",
            "effective_start": "Ngày bắt đầu áp dụng",
            "effective_end": "Ngày kết thúc áp dụng",
            "is_active": "Đang áp dụng",
            "note": "Ghi chú",
        }
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
            "effective_start": forms.DateInput(attrs={"type": "date"}),
            "effective_end": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["course_section"].queryset = CourseSection.objects.select_related(
            "course", "term", "lecturer__user"
        ).order_by("code")
        self.fields["classroom"].queryset = Classroom.objects.order_by("building", "code")


class AdminClassSessionForm(forms.ModelForm):
    class Meta:
        model = ClassSession
        fields = ("timetable", "session_date", "status", "topic", "note")
        labels = {
            "timetable": "Thời khóa biểu",
            "session_date": "Ngày học",
            "status": "Trạng thái",
            "topic": "Nội dung buổi học",
            "note": "Ghi chú",
        }
        widgets = {
            "session_date": forms.DateInput(attrs={"type": "date"}),
            "topic": forms.TextInput(attrs={"maxlength": 255}),
            "note": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["timetable"].queryset = Timetable.objects.select_related(
            "course_section__course",
            "course_section__term",
            "classroom",
        ).order_by("course_section__code", "weekday", "start_time")

    def clean(self):
        cleaned_data = super().clean()

        if not self.instance.pk:
            return cleaned_data

        attendance_session = AttendanceSession.objects.filter(
            class_session_id=self.instance.pk,
        ).first()

        if attendance_session:
            timetable = cleaned_data.get("timetable")
            session_date = cleaned_data.get("session_date")
            status = cleaned_data.get("status")

            if (
                timetable
                and session_date
                and (
                    timetable.pk != self.instance.timetable_id
                    or session_date != self.instance.session_date
                )
            ):
                raise forms.ValidationError(
                    "Buổi học đã có phiên điểm danh, không thể thay đổi lịch hoặc ngày học."
                )

            if (
                status == ClassSessionStatus.CANCELLED
                and attendance_session.status == AttendanceSessionStatus.OPEN
            ):
                raise forms.ValidationError("Vui lòng đóng phiên điểm danh trước khi hủy buổi học.")

        return cleaned_data
