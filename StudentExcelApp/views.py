from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from .models import *


# Create your views.
def home(request):
    return render(request,'home.html')


# Login page View
def login_page(request):
    if request.method == "POST":
        username = request.POST.get("email")
        password = request.POST.get("password")

        print("Username:", username)
        print("Password:", password)

        user = authenticate(
            request,
            username=username,
            password=password
        )

        

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        messages.error(request, "Invalid Email or Password")
    user = User.objects.get(username = "dhanusharumugam245@gmail.com")
    print(user.password)
    return render(request, "login.html")

# Register Page VIew
def register(request):
    if request.method == "POST":
        username = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get("confirm_password")

        try:
            validate_email(username)
        except ValidationError:
            messages.error(request,"Enter a Valid Email")
            return redirect('register')

        allowed_domains = (
            '@gmail.com',
            '@yahoo.com',
            '@email.com'
        )

        if not username.endswith(allowed_domains):
            messages.error(request,"Enter A valid domain name Like @gmail,@yahoo and @email.com")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request,"User Already Exist")
            return redirect("register")

        if password != confirm_password:
            messages.error(request,"Password Mismatch")
            return redirect('register')
        
        User.objects.create_user(
            username=username,
            password=password
        )
        messages.success(request,"Registration Sucessfully")
        return redirect('login')
    return render(request,'register.html')

# Dashboard Page View
@login_required
def dashboard(request):
    students = Student.objects.all().order_by("student_id")

    context = {
        "students": students
    }

    return render(request, "dashboard.html", context)


def logout_view(request):

    logout(request)

    messages.success(request, "Logged out Successfully.")

    return redirect("login")