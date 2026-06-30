from django.urls import path
from .views import *

urlpatterns = [
    path("",home,name="home"),
    path("login/",login_page,name="login"),
    path("Register/",register,name="register"),
    path("dashboard/",dashboard,name="dashboard"),
]