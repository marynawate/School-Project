from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class Course(models.Model):
    code = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    credits = models.PositiveSmallIntegerField(default=3)
    instructor = models.CharField(max_length=100, blank=True)
    capacity = models.PositiveIntegerField(default=40)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.title}"

    def get_absolute_url(self):
        return reverse("course_detail", args=[self.pk])

    @property
    def seats_left(self):
        return max(self.capacity - self.enrollments.count(), 0)


class Student(models.Model):
    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="student_profile",
    )
    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
    address = models.CharField(max_length=200, blank=True)
    program = models.CharField(max_length=100, blank=True)
    year_of_study = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(8)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.full_name} ({self.student_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse("student_detail", args=[self.pk])

    @property
    def gpa(self):
        """Credit-weighted GPA on a 4.0 scale over graded enrollments."""
        graded = [e for e in self.enrollments.select_related("course") if e.score is not None]
        credits = sum(e.course.credits for e in graded)
        if not credits:
            return None
        points = sum(e.grade_point * e.course.credits for e in graded)
        return round(points / credits, 2)


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_on = models.DateField(auto_now_add=True)
    score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    class Meta:
        unique_together = ("student", "course")
        ordering = ["-enrolled_on"]

    def __str__(self):
        return f"{self.student} -> {self.course.code}"

    @property
    def letter(self):
        if self.score is None:
            return "—"
        s = float(self.score)
        for cutoff, letter in ((90, "A"), (80, "B"), (70, "C"), (60, "D")):
            if s >= cutoff:
                return letter
        return "F"

    @property
    def grade_point(self):
        return {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0}.get(self.letter, 0)


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "P", "Present"
        ABSENT = "A", "Absent"
        LATE = "L", "Late"

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="attendance")
    date = models.DateField()
    status = models.CharField(max_length=1, choices=Status.choices, default=Status.PRESENT)

    class Meta:
        unique_together = ("enrollment", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.enrollment} {self.date} {self.get_status_display()}"
