from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Student, LoginHistory

# Student admin with history
@admin.register(Student)
class StudentAdmin(SimpleHistoryAdmin):
    list_display = (
        "studentid",
        "studentname",
        "email",
        "course",
        "department",
    )

# Historical Student model
HistoricalStudent = Student.history.model

@admin.register(HistoricalStudent)
class HistoricalStudentAdmin(admin.ModelAdmin):
    list_display = (
        "history_date",
        "history_type",
        "history_user",
        "studentid",
        "studentname",
        "email",
        "course",
        "department",
    )
    search_fields = (
        "studentid",
        "studentname",
        "email",
    )
    list_filter = (
        "history_type",
        "history_date",
    )
    ordering = ("-history_date",)

# Login History
@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "login_time",
        "logout_time",
    )
    search_fields = ("username",)
    list_filter = ("login_time",)