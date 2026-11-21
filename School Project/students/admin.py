from django.contrib import admin

from .models import Attendance, Course, Enrollment, Student

admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Attendance)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "last_name", "first_name", "email", "program", "is_active")
    search_fields = ("student_id", "first_name", "last_name", "email")
