from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords

#upload models
class UploadFile(models.Model):
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)


# Students Models.
class Student(models.Model):

    upload = models.ForeignKey(
        UploadFile,
        on_delete=models.CASCADE,
        related_name="students"
    )

    studentid = models.CharField(max_length=20)
    studentname = models.CharField(max_length=100)
    email = models.EmailField()
    course = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    
    history = HistoricalRecords()

    def __str__(self):
        return self.studentname
    

# Email Log Model
class EmailLog(models.Model):

    EMAIL_STATUS = (
        ("sent", "Sent"),
        ("failed", "Failed"),
    )

    to_email = models.EmailField()

    cc_email = models.TextField(
        blank=True,
        null=True
    )

    subject = models.CharField(
        max_length=255
    )

    email_status = models.CharField(
        max_length=10,
        choices=EMAIL_STATUS
    )

    sent_at = models.DateTimeField(
        auto_now_add=True
    )

    related_object_id = models.IntegerField()

    def __str__(self):
        return f"{self.to_email} - {self.email_status}"
