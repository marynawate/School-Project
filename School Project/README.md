# Student Management System (Django)

**Problem:** schools track students, courses, grades and attendance in scattered spreadsheets.
**Users:** administrators/registrars (staff) and students.
**What users can do:**

| Role | Capabilities |
|------|--------------|
| Admin (staff) | Dashboard stats; full CRUD on students and courses; search + pagination; enroll/remove students; enter grades; record attendance |
| Student | Sign up (linked to a profile), see own dashboard, GPA and grades; browse/search courses; self-enroll/drop (capacity enforced); view own profile |

Course concepts covered: HTML/CSS (Bootstrap), Django views/templates, forms and validation, ORM/database (SQLite), CRUD, authentication and role-based authorization, CSRF/security, JSON APIs (`/api/students/`, `/api/courses/`), tests.

## Run

```
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo      # optional demo data + accounts
python manage.py runserver
```

Open http://127.0.0.1:8000/. Demo logins: `admin / admin123`, `student1 / student123`.
Run tests with `python manage.py test`.

## Structure
- `students/models.py` – Student, Course, Enrollment (score → letter/GPA), Attendance
- `students/views.py`, `urls.py`, `forms.py` – app logic
- `templates/`, `static/` – UI

## Before deploying
Set a new `SECRET_KEY`, `DEBUG = False`, and `ALLOWED_HOSTS` in `config/settings.py`; change the demo passwords.
