from django.db import models
from django.contrib.auth.models import User

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

    def __str__(self):
        return self.studentname
    


