from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Attendance, Course, Enrollment, Student


class StyledMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            w = f.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs["class"] = "form-check-input"
            elif isinstance(w, forms.Select):
                w.attrs["class"] = "form-select"
            else:
                w.attrs["class"] = "form-control"


class StudentForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Student
        exclude = ["user", "created_at"]
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}


class CourseForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Course
        fields = "__all__"
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class GradeForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ["score"]


class AttendanceForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["date", "status"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}


class EnrollStudentForm(StyledMixin, forms.Form):
    student = forms.ModelChoiceField(queryset=Student.objects.filter(is_active=True))


class SignUpForm(StyledMixin, UserCreationForm):
    first_name = forms.CharField(max_length=60)
    last_name = forms.CharField(max_length=60)
    email = forms.EmailField()
    student_id = forms.CharField(max_length=20)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def clean_student_id(self):
        sid = self.cleaned_data["student_id"].strip()
        existing = Student.objects.filter(student_id=sid).first()
        if existing and existing.user_id:
            raise forms.ValidationError("This student ID is already registered.")
        return sid

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        d = self.cleaned_data
        # Link to a record created earlier by an administrator, or create a new one.
        student = Student.objects.filter(student_id=d["student_id"]).first() or Student(
            student_id=d["student_id"], email=d["email"])
        student.user = user
        student.first_name, student.last_name = d["first_name"], d["last_name"]
        student.save()
        return user
