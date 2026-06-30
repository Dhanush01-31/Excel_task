from django.db import models

# Students Models.
class Student(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    student_name = models.CharField(max_length=100)
    email = models.EmailField()
    course = models.CharField(max_length=100)
    department = models.CharField(max_length=100)

    def __str__(self):
        return self.student_name
