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
from django.db.models import Count
from django.db import connection
from django.db import transaction


# Create your views.
# def home(request):
#     return render(request,'home.html')


# Login page View
def login_page(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        login_input = request.POST.get("login")

        password = request.POST.get("password")

        # Check whether the user entered an email
        if "@" in login_input:

            try:
                user = User.objects.get(email=login_input)

                username = user.username

            except User.DoesNotExist:

                username = login_input

        else:

            username = login_input

        user = authenticate(

            request,

            username=username,

            password=password

        )

        if user:

            login(request, user)

            return redirect("dashboard")

        messages.error(
            request,
            "Invalid Username/Email or Password."
        )

    return render(request, "login.html")

# Register Page VIew
def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        username = request.POST.get("username").strip()
        email = request.POST.get("email").strip()

        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request,"Enter a Valid Email")
            return redirect('register')

        allowed_domains = (
            '@gmail.com',
            '@yahoo.com',
            '@email.com'
        )

        if not email.lower().endswith(allowed_domains):
            messages.error(request,"Enter A valid domain name Like @gmail,@yahoo and @email.com")
            return redirect('register')

        if User.objects.filter(email=email).exists():

            messages.error(
                request,
                "Email already registered."
            )

            return redirect("register")

        
        if User.objects.filter(username=username).exists():
            messages.error(request,"User Already Exist")
            return redirect("register")
        

        if password != confirm_password:
            messages.error(request,"Password Mismatch")
            return redirect('register')
        
        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        messages.success(request,"Registration Sucessfully")
        return redirect('login')
    return render(request,'register.html')

# Validators
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

    uploads = UploadFile.objects.filter(uploaded_by=request.user).annotate(total_records=Count("students"))

    mandatory_fields = [
        "studentid",
        "studentname",
        "email",
        "course",
        "department",
    ]

    if request.method == "POST":

        excel_file = request.FILES.get("excel_file")

        # File Validation
        if not excel_file:
            messages.error(request, "Please choose an Excel file.")
            return redirect("dashboard")

        if not excel_file.name.lower().endswith((".xlsx", ".xls")):
            messages.error(request, "Only Excel files are allowed.")
            return redirect("dashboard")

        try:
            df = pd.read_excel(excel_file)
        except Exception:
            messages.error(request, "Unable to read the Excel file.")
            return redirect("dashboard")

        # Convert all column names to lowercase
        df.columns = df.columns.str.strip().str.lower()
        
        # Column order checking.
        expected_columns = [
                "studentid",
                "studentname",
                "email",
                "course",
                "department",
            ]
        if list(df.columns) != expected_columns:
            messages.error(request,f"Invalid Template  Expected Columns: {', '.join(expected_columns)}")
            
            return redirect('dashboard')
            
        # Check Missing Columns
        missing_columns = []

        for column in mandatory_fields:
            if column not in df.columns:
                missing_columns.append(column)

        if missing_columns:
            messages.error(
                request,
                "Missing Columns: " + ", ".join(missing_columns)
            )
            return redirect("dashboard")

        validation_errors = []

        seen_student_ids = set()
        
        invalid_rows = []
        
        students_objects = []

        # Validate each row
        for index, row in df.iterrows():

            row_number = index + 2

            student_id = str(row["studentid"]).strip()
            student_name = str(row["studentname"]).strip()
            email = str(row["email"]).strip()
            course = str(row["course"]).strip()
            department = str(row["department"]).strip()

            # Mandatory Validation
            if pd.isna(row["studentid"]) or student_id == "":
                validation_errors.append(
                    f"Row {row_number}: Student ID is mandatory."
                )
                invalid_rows.append({
        "row": row_number,
        "studentid": student_id,
        "studentname": student_name,
        "email": email,
        "course": course,
        "department": department,
        "error": "Student ID is mandatory"
    })
                continue

            if pd.isna(row["studentname"]) or student_name == "":
                validation_errors.append(
                    f"Row {row_number}: Student Name is mandatory."
                )
                invalid_rows.append({
        "row": row_number,
        "studentid": student_id,
        "studentname": student_name,
        "email": email,
        "course": course,
        "department": department,
        "error": "Student Name is mandatory"
    })
                continue

            if pd.isna(row["email"]) or email == "":
                validation_errors.append(
                    f"Row {row_number}: Email is mandatory."
                )
                invalid_rows.append({
        "row": row_number,
        "studentid": student_id,
        "studentname": student_name,
        "email": email,
        "course": course,
        "department": department,
        "error": "Email ID is mandatory"
    })
                continue

            if pd.isna(row["course"]) or course == "":
                validation_errors.append(
                    f"Row {row_number}: Course is mandatory."
                )
                invalid_rows.append({
        "row": row_number,
        "studentid": student_id,
        "studentname": student_name,
        "email": email,
        "course": course,
        "department": department,
        "error": "course is mandatory"
    })
                continue

            if pd.isna(row["department"]) or department == "":
                validation_errors.append(
                    f"Row {row_number}: Department is mandatory."
                )
                invalid_rows.append({
        "row": row_number,
        "studentid": student_id,
        "studentname": student_name,
        "email": email,
        "course": course,
        "department": department,
        "error": "Department is mandatory"
    })
                continue

            # Student Name Validation
            if not validate_student_name(student_name):
                validation_errors.append(
                    f"Row {row_number}: Invalid Student Name."
                )
                invalid_rows.append({
        "row": row_number,
        "studentid": student_id,
        "studentname": student_name,
        "email": email,
        "course": course,
        "department": department,
        "error": "Invalid Student Name"
    })
                continue

            # Email Validation
            if not validate_student_email(email):
                validation_errors.append(
                    f"Row {row_number}: Invalid Email."
                )
                invalid_rows.append({

                    "row": row_number,

                    "studentid": student_id,

                    "studentname": student_name,

                    "email": email,

                    "course": course,

                    "department": department,

                    "error": "Invalid Email"

                    })
                continue

            # Student ID Validation
            if not validate_student_id(student_id):
                validation_errors.append(
                    f"Row {row_number}: Invalid Student ID Format."
                )
                invalid_rows.append({

                "row": row_number,

                "studentid": student_id,

                "studentname": student_name,

                "email": email,

                "course": course,

                "department": department,

                "error": "Invalid Student Id"

                })
                continue

            # Duplicate in Excel
            if student_id in seen_student_ids:
                validation_errors.append(
                    f"Row {row_number}: Duplicate Student ID in Excel."
                )
                invalid_rows.append({
        "row": row_number,
        "studentid": student_id,
        "studentname": student_name,
        "email": email,
        "course": course,
        "department": department,
        "error": "Duplicate Student ID in Excel."
    })
                continue

            seen_student_ids.add(student_id)

            # Duplicate in Database
            if Student.objects.filter(
                upload__uploaded_by=request.user,
                studentid=student_id
            ).exists():

                validation_errors.append(
                    f"Row {row_number}: Student ID already exists in database."
                )
                invalid_rows.append({
        "row": row_number,
        "studentid": student_id,
        "studentname": student_name,
        "email": email,
        "course": course,
        "department": department,
        "error": "Student ID already exists in database"
    })
                continue

            # Course Validation
            if not validate_course(course):
                validation_errors.append(
                    f"Row {row_number}: Invalid Course."
                )
                invalid_rows.append({
        "row": row_number,
        "studentid": student_id,
        "studentname": student_name,
        "email": email,
        "course": course,
        "department": department,
        "error": "Invalid Course."
    })
                continue

            # Department Validation
            if not validate_department(department):
                validation_errors.append(
                    f"Row {row_number}: Invalid Department."
                )
                invalid_rows.append({
        "row": row_number,
        "studentid": student_id,
        "studentname": student_name,
        "email": email,
        "course": course,
        "department": department,
        "error": "Invalid Course."
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

        # If there are validation errors, don't save anything
        if validation_errors:

            context = {'uploads':uploads,
                       'invalid_rows':invalid_rows}
            
            for error in validation_errors:
                messages.error(request, error)
            

            return render(request,"dashboard.html",context)

        # Save everything in one transaction
        with transaction.atomic():

            upload = UploadFile.objects.create(

                uploaded_by=request.user,
                filename=excel_file.name

            )

            for student in students_objects:
                student.upload = upload

            Student.objects.bulk_create(students_objects)

        messages.success(
            request,
            f"{len(students_objects)} students uploaded successfully."
        )

        return redirect("dashboard")

    context = {
        "uploads": uploads
    }

    return render(request, "dashboard.html", context)


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

        student.studentname = request.POST.get("studentname")
        student.email = request.POST.get("email")
        student.course = request.POST.get("course")
        student.department = request.POST.get("department")

        student.save()

        messages.success(request, "Student updated successfully.")

        return redirect("dashboard")

# delete view.
@login_required
def delete_student(request, id):

    student = get_object_or_404(Student, id=id)

    student.delete()

    messages.success(request, "Student deleted successfully.")

    return redirect("dashboard")

# student records view.
def student_records(request, upload_id):

    upload = get_object_or_404(
        UploadFile,
        id=upload_id,
        uploaded_by=request.user
    )

    students = Student.objects.filter(
        upload=upload
    )

    return render(
        request,
        "student_records.html",
        {
            "upload": upload,
            "students": students
        }
    )