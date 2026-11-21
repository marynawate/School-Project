from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Course, Enrollment, Student


class SMSTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin", password="pw", is_staff=True)
        self.u = User.objects.create_user("stu", password="pw")
        self.student = Student.objects.create(user=self.u, student_id="S1", first_name="A",
                                              last_name="B", email="a@b.com")
        self.course = Course.objects.create(code="CS101", title="Intro", credits=3, capacity=1)

    def test_login_required(self):
        self.assertEqual(self.client.get(reverse("student_list")).status_code, 302)

    def test_student_cannot_list_students(self):
        self.client.login(username="stu", password="pw")
        self.assertEqual(self.client.get(reverse("student_list")).status_code, 403)

    def test_admin_crud(self):
        self.client.login(username="admin", password="pw")
        r = self.client.post(reverse("student_add"), {
            "student_id": "S2", "first_name": "C", "last_name": "D", "email": "c@d.com",
            "year_of_study": 1, "is_active": "on"})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Student.objects.filter(student_id="S2").exists())

    def test_self_enroll_and_capacity(self):
        self.client.login(username="stu", password="pw")
        self.client.post(reverse("self_enroll", args=[self.course.pk]))
        self.assertEqual(Enrollment.objects.count(), 1)
        self.assertEqual(self.course.seats_left, 0)

    def test_gpa(self):
        Enrollment.objects.create(student=self.student, course=self.course, score=85)
        self.assertEqual(self.student.gpa, 3.0)

    def test_signup_creates_profile(self):
        r = self.client.post(reverse("signup"), {
            "username": "new", "first_name": "N", "last_name": "M", "email": "n@m.com",
            "student_id": "S9", "password1": "Str0ng!pass99", "password2": "Str0ng!pass99"})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Student.objects.get(student_id="S9").user)
