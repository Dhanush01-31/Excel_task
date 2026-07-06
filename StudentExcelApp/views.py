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
from django.utils.http import url_has_allowed_host_and_scheme
#-----------------------------------------------
#celery import
import os
import uuid
from django.conf import settings
from .tasks import send_invalid_records_email
#-----------------------------------------------
# Forgot Email Import
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse
from .tasks import send_password_reset_email
from django.utils.encoding import force_str
from django.contrib.auth.hashers import make_password
#------------------------------------------------


# Home view.
def home(request):
    return render(request,'home.html')


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

            next_url = request.GET.get("next") or request.POST.get("next")
            
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
                ):
                return redirect(next_url)
            return redirect('dashboard')
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
    uploads = (
        UploadFile.objects.filter(uploaded_by=request.user)
        .annotate(total_records=Count("students"))
        .order_by("-uploaded_at")
    )

    expected_columns = [
        "studentid",
        "studentname",
        "email",
        "course",
        "department",
    ]

    if request.method == "POST":
        excel_file = request.FILES.get("excel_file")

        if not excel_file:
            messages.error(request, "Please choose an Excel file.")
            return render(request, "dashboard.html", {"uploads": uploads})

        if not excel_file.name.lower().endswith((".xlsx", ".xls")):
            messages.error(request, "Only Excel files are allowed.")
            return render(request, "dashboard.html", {"uploads": uploads})

        try:
            df = pd.read_excel(excel_file, sheet_name=0)
        except Exception:
            messages.error(request, "Unable to read the Excel file.")
            return render(request, "dashboard.html", {"uploads": uploads})

        if df.empty:
            messages.error(request, "The uploaded Excel file is empty.")
            return render(request, "dashboard.html", {"uploads": uploads})

        df.columns = df.columns.astype(str).str.strip().str.lower()

        if list(df.columns) != expected_columns:
            messages.error(
                request,
                f"Invalid template. Expected columns in this order: {', '.join(expected_columns)}"
            )
            return render(request, "dashboard.html", {"uploads": uploads})

        seen_student_ids = set()
        invalid_rows = []
        valid_students = []

        uploaded_student_ids = df["studentid"].dropna().astype(str).str.strip().tolist()
        existing_ids = set(
            Student.objects.filter(
                upload__uploaded_by=request.user,
                studentid__in=uploaded_student_ids,
            ).values_list("studentid", flat=True)
        )

        for index, row in df.iterrows():
            row_number = index + 2

            student_id = "" if pd.isna(row["studentid"]) else str(row["studentid"]).strip()
            student_name = "" if pd.isna(row["studentname"]) else str(row["studentname"]).strip()
            email = "" if pd.isna(row["email"]) else str(row["email"]).strip()
            course = "" if pd.isna(row["course"]) else str(row["course"]).strip()
            department = "" if pd.isna(row["department"]) else str(row["department"]).strip()

            base_row = {
                "row": row_number,
                "studentid": student_id,
                "studentname": student_name,
                "email": email,
                "course": course,
                "department": department,
            }

            if not student_id:
                invalid_rows.append({**base_row, "error": "Student ID is mandatory"})
                continue
            if not student_name:
                invalid_rows.append({**base_row, "error": "Student Name is mandatory"})
                continue
            if not email:
                invalid_rows.append({**base_row, "error": "Email is mandatory"})
                continue
            if not course:
                invalid_rows.append({**base_row, "error": "Course is mandatory"})
                continue
            if not department:
                invalid_rows.append({**base_row, "error": "Department is mandatory"})
                continue

            if not validate_student_id(student_id):
                invalid_rows.append({**base_row, "error": "Invalid Student ID. Example: STU001"})
                continue

            if not validate_student_name(student_name):
                invalid_rows.append({**base_row, "error": "Invalid Student Name. Example: Ashokkumar"})
                continue

            if not validate_student_email(email):
                invalid_rows.append({**base_row, "error": "Invalid Email. Example: joe234@gmail.com"})
                continue

            if not validate_course(course):
                invalid_rows.append({**base_row, "error": "Invalid Course. Example: MCA or BCA"})
                continue

            if not validate_department(department):
                invalid_rows.append({**base_row, "error": "Invalid Department. Example: Mathematics"})
                continue

            if student_id in seen_student_ids:
                invalid_rows.append({**base_row, "error": "Duplicate Student ID in Excel file"})
                continue
            seen_student_ids.add(student_id)

            if student_id in existing_ids:
                invalid_rows.append({**base_row, "error": "Student ID already exists in database"})
                continue

            valid_students.append(
                Student(
                    studentid=student_id,
                    studentname=student_name,
                    email=email,
                    course=course,
                    department=department,
                )
            )

        upload = None
        
        if valid_students:
            with transaction.atomic():
                upload = UploadFile.objects.create(
                    uploaded_by=request.user,
                    filename=excel_file.name,
                )
                for student in valid_students:
                    student.upload = upload
                Student.objects.bulk_create(valid_students, batch_size=500)
                
        # Send invalid records through email
        if invalid_rows:

            error_df = pd.DataFrame(invalid_rows)
            os.makedirs(os.path.join(
                settings.MEDIA_ROOT, "error_reports"),
                        exist_ok=True,)

            file_name = f"errors_{uuid.uuid4().hex}.xlsx"

            file_path = os.path.join(
            settings.MEDIA_ROOT,
            "error_reports",
            file_name,
            )

            error_df.to_excel(file_path, index=False)

            related_id = upload.id if upload else 0

            send_invalid_records_email.delay(
            request.user.email,
            file_path,
            related_id,
            )                                                        

        if invalid_rows and valid_students:
            messages.warning(
                request,
                f"{len(valid_students)} rows uploaded successfully. {len(invalid_rows)} rows failed."
            )
        elif invalid_rows and not valid_students:
            messages.error(
                request,
                f"Upload failed. {len(invalid_rows)} rows are invalid."
            )
        else:
            messages.success(
                request,
                f"{len(valid_students)} rows uploaded successfully."
            )

        uploads = (
            UploadFile.objects.filter(uploaded_by=request.user)
            .annotate(total_records=Count("students"))
            .order_by("-uploaded_at")
        )

        context = {
            "uploads": uploads,
            "invalid_rows": invalid_rows,
        }
        return render(request, "dashboard.html", context)

    return render(request, "dashboard.html", {"uploads": uploads})


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

        studentname = request.POST.get("studentname", "").strip()
        email = request.POST.get("email", "").strip()
        course = request.POST.get("course", "").strip()
        department = request.POST.get("department", "").strip()

        # -----------------------
        # Name Validation
        # -----------------------
        if not studentname:
            messages.error(request, "Student Name is required.")
            return redirect("student_records", upload_id=student.upload.id)

        if len(studentname) > 100:
            messages.error(request, "Student Name cannot exceed 100 characters.")
            return redirect("student_records", upload_id=student.upload.id)

        if not re.fullmatch(r"[A-Za-z ]+", studentname):
            messages.error(request, "Student Name should contain only alphabets.")
            return redirect("student_records", upload_id=student.upload.id)

        # -----------------------
        # Email Validation
        # -----------------------
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Invalid Email Address.")
            return redirect("student_records", upload_id=student.upload.id)

        # Duplicate Email
        if Student.objects.exclude(id=student.id).filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("student_records", upload_id=student.upload.id)

        # -----------------------
        # Course Validation
        # -----------------------
        if not course:
            messages.error(request, "Course is required.")
            return redirect("student_records", upload_id=student.upload.id)

        if len(course) > 100:
            messages.error(request, "Course cannot exceed 100 characters.")
            return redirect("student_records", upload_id=student.upload.id)

        # -----------------------
        # Department Validation
        # -----------------------
        if not department:
            messages.error(request, "Department is required.")
            return redirect("student_records", upload_id=student.upload.id)

        if len(department) > 100:
            messages.error(request, "Department cannot exceed 100 characters.")
            return redirect("student_records", upload_id=student.upload.id)

        # -----------------------
        # Save
        # -----------------------
        student.studentname = studentname
        student.email = email
        student.course = course
        student.department = department

        student.save()

        messages.success(request, "Student updated successfully.")

        return redirect("student_records", upload_id=student.upload.id)

# delete view.
@login_required
def delete_student(request, id):

    student = get_object_or_404(Student, id=id)

    student.delete()

    messages.success(request, "Student deleted successfully.")

    return redirect("dashboard")

# student records view.
@login_required
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
    
    
# Forgot_email Password View.
def forgot_password(request):

    if request.method == "POST":

        email = request.POST.get("email").strip()

        if not User.objects.filter(email=email).exists():

            messages.error(request, "Email does not exist.")

            return redirect("forgot_password")

        user = User.objects.get(email=email)

        # Generate reset link here
        token = PasswordResetTokenGenerator().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = request.build_absolute_uri(
            reverse(
            "reset_password",
            kwargs={
                "uidb64": uid,
                "token": token,
                },
            )
        )
        send_password_reset_email.delay(

            user.email,

            reset_link,

        )
        
        messages.success(request,"Password reset link has been sent to your email.")
        return redirect("login")
    
    return render(request, "forgot_password.html")

# Reset Password View
def reset_password(request, uidb64, token):

    try:

        uid = force_str(urlsafe_base64_decode(uidb64))

        user = User.objects.get(pk=uid)

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):

        user = None

    if user is None:

        messages.error(request, "Invalid password reset link.")

        return redirect("login")

    if not PasswordResetTokenGenerator().check_token(user, token):

        messages.error(request, "Password reset link has expired or is invalid.")

        return redirect("login")

    if request.method == "POST":

        password1 = request.POST.get("password1", "").strip()

        password2 = request.POST.get("password2", "").strip()

        if not password1:

            messages.error(request, "New Password is required.")

            return render(request, "reset_password.html")

        if not password2:

            messages.error(request, "Confirm Password is required.")

            return render(request, "reset_password.html")

        if password1 != password2:

            messages.error(request, "Passwords do not match.")

            return render(request, "reset_password.html")

        user.password = make_password(password1)

        user.save()

        messages.success(
            request,
            "Password changed successfully. Please login."
        )

        return redirect("login")

    return render(request, "reset_password.html")
#--------------------------------------------------------------------------------------------------

# 404 and 500 error views
def custom_404(request, exception):
    return render(request, "404.html", status=404)

def custom_500(request):
    return render(request, "500.html", status=500)