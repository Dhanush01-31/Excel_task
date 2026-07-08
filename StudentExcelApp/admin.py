from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import *

admin.site.register(Student, SimpleHistoryAdmin)

# Register the historical model
HistoricalStudent = Student.history.model
admin.site.register(HistoricalStudent)

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ("username", "login_time", "logout_time")
    search_fields = ("username",)
    list_filter = ("login_time",)