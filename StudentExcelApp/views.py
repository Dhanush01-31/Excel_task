from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from .models import *
import openpyxl #--> pyxl
import pandas as pd #-->  pandas
import re

# Create your views.
# def home(request):
#     return render(request,'home.html')


# Login page View
def login_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
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
    return render(request, "login.html")

# Register Page VIew
def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
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


def validate_student_name(name):

    name = str(name).strip()

    return bool(re.fullmatch(r"[A-Za-z ]+", name))


def validate_student_email(email):

    try:
        validate_email(str(email).strip())
        return True

    except ValidationError:
        return False

def validate_student_id(studentid):

    return bool(
        re.fullmatch(r"STU\d{3}", studentid)
    )

def validate_course(course):

    return bool(
        re.fullmatch(r"[A-Za-z ]+", course)
    )
    
def validate_department(department):

    return bool(
        re.fullmatch(r"[A-Za-z ]+", department)
    )

# Dashboard Page View
@login_required
def dashboard(request):
    students = Student.objects.all().order_by('id')

    mandatory_fields = [
        "studentid",
        "studentname",
        "email",
        "course",
        "department",
    ]

    if request.method == "POST":
        excel_file = request.FILES.get('excel_file')
        

        if not excel_file:
            messages.error(request,"please Choose an Excel File")
            return redirect('dashboard')
        
        if not excel_file.name.lower().endswith((".xlsx",".xls")):
            messages.error(request,"Only Excel Files are allowed")
            return redirect('dashboard')

        df = pd.read_excel(excel_file)

        df.columns = ( df.columns.str.strip().str.lower() )


        # Missing columns Validation
        missing_columns = []

        for column in mandatory_fields:
            if column not in df.columns:
                missing_columns.append(column)

        if missing_columns:
            messages.error(request,"Missing Columns :"+",".join(missing_columns))
            return redirect('dashboard')
        
        errors = []

        for index,row in df.iterrows():
            for field in mandatory_fields:
                value = row[field]

                if pd.isna(value) or str(value).strip()=="":
                    errors.append(
                        f"ROW {index+2} : {field} is mandatory"
                    )
        
        if errors:
            for error in errors:
                messages.error(request,error)
            return redirect('dashboard')
        
        # Bulk Updation 
        students_objects = []

        validation_errors = []
        
        seen_student_ids = set()

        for index, row in df.iterrows():

            row_number = index + 2

            student_id = str(row["studentid"]).strip()
            student_name = str(row["studentname"]).strip()
            email = str(row["email"]).strip()
            course = str(row["course"]).strip()
            department = str(row["department"]).strip()

            
            # Mandatory field validation
            if not student_id:

                validation_errors.append({
                    "row": row_number,
                    "field": "Student ID",
                    "value": "",
                    "error": "Student ID is mandatory"
                })

                continue

            if not student_name:

                validation_errors.append({
                    "row": row_number,
                    "field": "Student Name",
                    "value": "",
                    "error": "Student Name is mandatory"
                })

                continue

            if not email:

                validation_errors.append({
                    "row": row_number,
                    "field": "Email",
                    "value": "",
                    "error": "Email is mandatory"
            })

                continue

            if not course:

                validation_errors.append({
                    "row": row_number,
                    "field": "Course",
                    "value": "",
                    "error": "Course is mandatory"
                    })

                continue

            if not department:

                validation_errors.append({
                    "row": row_number,
                    "field": "Department",
                    "value": "",
                    "error": "Department is mandatory"
                })

                continue

            # Student Name Validation
            if not validate_student_name(student_name):

                validation_errors.append({

                    "row": row_number,

                    "field": "Student Name",

                    "value": student_name,

                    "error": "Invalid Student Name"

                })

                continue

            # Email Validation
            if not validate_student_email(email):

                validation_errors.append({

                    "row": row_number,

                    "field": "Email",

                    "value": email,

                    "error": "Invalid Email"

                })

                continue
            
            # student_id_validation
            if not validate_student_id(student_id):
                validation_errors.append({
                    "row": row_number,
                     "field": "Student ID",
                     "value": student_id,
                      "error": "Invalid Student ID Format",
                       })
                continue
            # Student_id in uploaded excel.
            if student_id in seen_student_ids:
                validation_errors.append({
                    "row": row_number,
                    "field": "Student ID",
                    "value": student_id,
                    "error": "Duplicate Student ID in uploaded Excel"
                })
                continue
            seen_student_ids.add(student_id)
            
            #Duplicate Student Id check
            if Student.objects.filter(studentid=student_id).exists():
                validation_errors.append({
                    "row": row_number,
                    "field": "Student ID",
                    "value": student_id,
                    "error": "Student ID already exists in database"
                })
                continue
           
           # student_Validate_course
            if not validate_course(course):
                validation_errors.append({
                    "row":row_number,
                    "field": "Course",
                     "value": course,
                     "error": "Invalid Course"
                })
                continue

            # Student_validate_department
            if not validate_department(department):
                validation_errors.append({
                    "row": row_number,
                     "field": "Department",
                      "value": department,
                      "error": "Invalid Department"    
                })
                continue

            
            
            students_objects.append(

                Student(

                    studentid=student_id,

                    studentname=student_name,

                    email=email,

                    course=course,

                    department=department,

                )

            )

        # Save only valid students
        if students_objects:    
            Student.objects.bulk_create(students_objects)

        # Success message
            messages.success(
                request,
            f"{len(students_objects)} records uploaded successfully."
            )
        else:
            messages.warning(request,"No valid records Found to upload.")

        # Show validation errors
        for error in validation_errors:

            messages.warning(

                request,

                f"Row {error['row']} | {error['field']} | Value: {error['value']} | {error['error']}"

                )

        return redirect("dashboard")
    
    context = {'students':students}
    return render(request,"dashboard.html",context)


# Logout View
def logout_view(request):

    logout(request)

    messages.success(request, "Logged out Successfully.")

    return redirect("login")

# update view.
from django.shortcuts import get_object_or_404

@login_required
def update_student(request, id):

    student = get_object_or_404(Student, id=id)

    if request.method == "POST":

        studentid = request.POST.get("studentid")

        # Check duplicate student id
        if Student.objects.filter(studentid=studentid).exclude(id=id).exists():

            messages.error(
                request,
                "Student ID already exists."
            )

            return redirect("dashboard")

        student.studentid = studentid
        student.studentname = request.POST.get("studentname")
        student.email = request.POST.get("email")
        student.course = request.POST.get("course")
        student.department = request.POST.get("department")

        student.save()

        messages.success(
            request,
            "Student updated successfully."
        )

        return redirect("dashboard")
    context={'student':student}
    return render(request,"dashboard.html",context)


# delete view.
@login_required
def delete_student(request, id):

    student = get_object_or_404(Student, id=id)

    student.delete()

    messages.success(request, "Student deleted successfully.")

    return redirect("dashboard")
