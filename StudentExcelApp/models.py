from django.db import models

# Students Models.
class Student(models.Model):
    studentid = models.CharField(max_length=20, unique=True)
    studentname = models.CharField(max_length=100)
    email = models.EmailField()
    course = models.CharField(max_length=100)
    department = models.CharField(max_length=100)

    def __str__(self):
        return self.student_name


