from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate

# Create your views here.
def home(request):
    return render(request,'home.html')

def login_page(request):
    if request.method == "post":
        username = request.POST.get('email')
        password = request.POST.get('password')

    return render(request,"login.html")

def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request>POST.get('password')
        confirm_password = request.POST.get("confirm_password")

        try:
            validate_email(username)
        except ValidationError:
            messages.error(request,"Enter a Valid Email")
            return redirect(request,'register')

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
        
        User.objects.create(
            username=username,
            password=password
        )
        messages.success(request,"Registration Sucessfully")
        return redirect('register')
    return render(request,'register.html')

def dashboard(request):
    return render(request,"dashboard.html")