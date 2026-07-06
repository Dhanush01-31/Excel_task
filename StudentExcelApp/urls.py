from django.urls import path
from .views import *

urlpatterns = [
    path("",home,name="home"),
    path("login/",login_page,name="login"),
    path("register/",register,name="register"),
    path("dashboard/",dashboard,name="dashboard"),
    path("logout",logout_view,name="logout"),
    path("update/<int:id>/", update_student, name="update_student"),
    path("delete/<int:id>/", delete_student, name="delete_student"),
    path("student-records/<int:upload_id>/",student_records,name="student_records"),
    path("forgot-password/",forgot_password,name="forgot_password",),
    path("reset-password/<uidb64>/<token>/",reset_password,name="reset_password",),
]