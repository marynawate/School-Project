from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import IntegrityError
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import (AttendanceForm, CourseForm, EnrollStudentForm, GradeForm,
                    SignUpForm, StudentForm)
from .models import Attendance, Course, Enrollment, Student


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


def staff_only(view):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "Administrators only.")
            return redirect("dashboard")
        return view(request, *args, **kwargs)
    wrapper.__name__ = view.__name__
    return wrapper


def signup(request):
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.save())
        messages.success(request, "Welcome! Your account has been created.")
        return redirect("dashboard")
    return render(request, "registration/signup.html", {"form": form})


@login_required
def dashboard(request):
    if request.user.is_staff:
        ctx = {
            "student_count": Student.objects.filter(is_active=True).count(),
            "course_count": Course.objects.count(),
            "enrollment_count": Enrollment.objects.count(),
            "avg_score": Enrollment.objects.aggregate(a=Avg("score"))["a"],
            "popular": Course.objects.annotate(n=Count("enrollments")).order_by("-n")[:5],
            "recent": Student.objects.order_by("-created_at")[:5],
        }
        return render(request, "dashboard_admin.html", ctx)
    student = getattr(request.user, "student_profile", None)
    ctx = {"student": student,
           "enrollments": student.enrollments.select_related("course") if student else []}
    return render(request, "dashboard_student.html", ctx)


# ---- Students (admin CRUD) ----
class StudentList(StaffRequiredMixin, ListView):
    model = Student
    paginate_by = 10
    template_name = "students/student_list.html"

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) |
                           Q(student_id__icontains=q) | Q(email__icontains=q) |
                           Q(program__icontains=q))
        return qs

    def get_context_data(self, **kw):
        ctx = super().get_context_data(**kw)
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class StudentDetail(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Student
    template_name = "students/student_detail.html"

    def test_func(self):
        u = self.request.user
        return u.is_staff or getattr(u, "student_profile", None) == self.get_object()

    def get_context_data(self, **kw):
        ctx = super().get_context_data(**kw)
        ctx["enrollments"] = self.object.enrollments.select_related("course")
        return ctx


class StudentCreate(StaffRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = "form.html"
    extra_context = {"title": "Add student"}


class StudentUpdate(StaffRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = "form.html"
    extra_context = {"title": "Edit student"}


class StudentDelete(StaffRequiredMixin, DeleteView):
    model = Student
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("student_list")


# ---- Courses ----
class CourseList(LoginRequiredMixin, ListView):
    model = Course
    template_name = "courses/course_list.html"

    def get_queryset(self):
        qs = Course.objects.annotate(n=Count("enrollments"))
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(title__icontains=q) | Q(instructor__icontains=q))
        return qs

    def get_context_data(self, **kw):
        ctx = super().get_context_data(**kw)
        student = getattr(self.request.user, "student_profile", None)
        ctx["enrolled_ids"] = set(student.enrollments.values_list("course_id", flat=True)) if student else set()
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class CourseDetail(LoginRequiredMixin, DetailView):
    model = Course
    template_name = "courses/course_detail.html"

    def get_context_data(self, **kw):
        ctx = super().get_context_data(**kw)
        if self.request.user.is_staff:
            ctx["enrollments"] = self.object.enrollments.select_related("student")
            ctx["enroll_form"] = EnrollStudentForm()
        return ctx


class CourseCreate(StaffRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = "form.html"
    extra_context = {"title": "Add course"}


class CourseUpdate(StaffRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = "form.html"
    extra_context = {"title": "Edit course"}


class CourseDelete(StaffRequiredMixin, DeleteView):
    model = Course
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("course_list")


# ---- Enrollment ----
def _enroll(request, student, course):
    if course.seats_left <= 0:
        messages.error(request, f"{course.code} is full.")
        return
    try:
        Enrollment.objects.create(student=student, course=course)
        messages.success(request, f"{student.full_name} enrolled in {course.code}.")
    except IntegrityError:
        messages.info(request, "Already enrolled.")


@login_required
@require_POST
def self_enroll(request, pk):
    student = getattr(request.user, "student_profile", None)
    if not student:
        messages.error(request, "No student profile on this account.")
        return redirect("course_list")
    _enroll(request, student, get_object_or_404(Course, pk=pk))
    return redirect("course_list")


@login_required
@require_POST
def self_drop(request, pk):
    student = getattr(request.user, "student_profile", None)
    if student:
        Enrollment.objects.filter(student=student, course_id=pk).delete()
        messages.success(request, "Course dropped.")
    return redirect("course_list")


@staff_only
@require_POST
def admin_enroll(request, pk):
    course = get_object_or_404(Course, pk=pk)
    form = EnrollStudentForm(request.POST)
    if form.is_valid():
        _enroll(request, form.cleaned_data["student"], course)
    return redirect(course)


@staff_only
@require_POST
def unenroll(request, pk):
    e = get_object_or_404(Enrollment, pk=pk)
    course = e.course
    e.delete()
    messages.success(request, "Student removed from course.")
    return redirect(course)


@staff_only
def grade(request, pk):
    e = get_object_or_404(Enrollment.objects.select_related("student", "course"), pk=pk)
    form = GradeForm(request.POST or None, instance=e)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Grade saved.")
        return redirect(e.course)
    return render(request, "form.html", {"form": form, "title": f"Grade {e.student.full_name} - {e.course.code}"})


@staff_only
def attendance(request, pk):
    e = get_object_or_404(Enrollment.objects.select_related("student", "course"), pk=pk)
    form = AttendanceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        Attendance.objects.update_or_create(
            enrollment=e, date=form.cleaned_data["date"],
            defaults={"status": form.cleaned_data["status"]})
        messages.success(request, "Attendance recorded.")
        return redirect("attendance", pk=pk)
    return render(request, "attendance.html", {"form": form, "enrollment": e,
                                               "records": e.attendance.all()})


# ---- JSON API ----
@login_required
def api_students(request):
    if not request.user.is_staff:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    q = request.GET.get("q", "")
    qs = Student.objects.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) |
                                Q(student_id__icontains=q))[:50]
    return JsonResponse({"results": [
        {"id": s.pk, "student_id": s.student_id, "name": s.full_name, "email": s.email,
         "program": s.program, "gpa": s.gpa} for s in qs]})


@login_required
def api_courses(request):
    return JsonResponse({"results": [
        {"id": c.pk, "code": c.code, "title": c.title, "credits": c.credits,
         "instructor": c.instructor, "seats_left": c.seats_left} for c in Course.objects.all()]})
