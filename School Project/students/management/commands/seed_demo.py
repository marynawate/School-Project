import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from students.models import Course, Enrollment, Student


class Command(BaseCommand):
    help = "Load demo data and create admin/admin123 and student1/student123 accounts."

    def handle(self, *args, **opts):
        random.seed(1)
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin123")
        courses = [("CS101", "Intro to Programming", 3, "Dr. Mwangi"),
                   ("CS201", "Data Structures", 4, "Dr. Otieno"),
                   ("MA101", "Calculus I", 3, "Prof. Njeri"),
                   ("EN101", "Technical Writing", 2, "Ms. Achieng"),
                   ("CS301", "Web Development with Django", 4, "Dr. Kamau")]
        cs = [Course.objects.get_or_create(code=c, defaults=dict(
            title=t, credits=cr, instructor=i, description=f"{t} course."))[0]
            for c, t, cr, i in courses]
        names = [("Amina", "Hassan"), ("Brian", "Odhiambo"), ("Cynthia", "Wanjiku"),
                 ("David", "Mutua"), ("Esther", "Akinyi"), ("Felix", "Kiprop")]
        for n, (f, l) in enumerate(names, 1):
            s, _ = Student.objects.get_or_create(
                student_id=f"STU{n:03d}",
                defaults=dict(first_name=f, last_name=l, email=f"{f.lower()}@example.com",
                              program="Computer Science", year_of_study=random.randint(1, 4)))
            if n == 1 and not User.objects.filter(username="student1").exists():
                s.user = User.objects.create_user("student1", s.email, "student123",
                                                  first_name=f, last_name=l)
                s.save()
            for c in random.sample(cs, 3):
                Enrollment.objects.get_or_create(student=s, course=c, defaults=dict(
                    score=random.choice([None, 55, 68, 75, 82, 91])))
        self.stdout.write(self.style.SUCCESS("Demo data loaded."))
