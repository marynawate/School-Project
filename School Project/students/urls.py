from django.urls import path

from . import views as v

urlpatterns = [
    path("", v.dashboard, name="dashboard"),
    path("signup/", v.signup, name="signup"),

    path("students/", v.StudentList.as_view(), name="student_list"),
    path("students/add/", v.StudentCreate.as_view(), name="student_add"),
    path("students/<int:pk>/", v.StudentDetail.as_view(), name="student_detail"),
    path("students/<int:pk>/edit/", v.StudentUpdate.as_view(), name="student_edit"),
    path("students/<int:pk>/delete/", v.StudentDelete.as_view(), name="student_delete"),

    path("courses/", v.CourseList.as_view(), name="course_list"),
    path("courses/add/", v.CourseCreate.as_view(), name="course_add"),
    path("courses/<int:pk>/", v.CourseDetail.as_view(), name="course_detail"),
    path("courses/<int:pk>/edit/", v.CourseUpdate.as_view(), name="course_edit"),
    path("courses/<int:pk>/delete/", v.CourseDelete.as_view(), name="course_delete"),
    path("courses/<int:pk>/enroll/", v.self_enroll, name="self_enroll"),
    path("courses/<int:pk>/drop/", v.self_drop, name="self_drop"),
    path("courses/<int:pk>/add-student/", v.admin_enroll, name="admin_enroll"),

    path("enrollments/<int:pk>/remove/", v.unenroll, name="unenroll"),
    path("enrollments/<int:pk>/grade/", v.grade, name="grade"),
    path("enrollments/<int:pk>/attendance/", v.attendance, name="attendance"),

    path("api/students/", v.api_students, name="api_students"),
    path("api/courses/", v.api_courses, name="api_courses"),
]
