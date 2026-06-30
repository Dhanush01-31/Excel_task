from django.urls import path
from .views import *

urlpatterns = [
    path("",home,name="home"),
    path("login/",login_page,name="login"),
    path("register/",register,name="register"),
    path("dashboard/",dashboard,name="dashboard"),
    path("logout",logout_view,name="logout"),
]