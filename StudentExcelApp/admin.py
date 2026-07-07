from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Student

admin.site.register(Student, SimpleHistoryAdmin)

# Register the historical model
HistoricalStudent = Student.history.model
admin.site.register(HistoricalStudent)