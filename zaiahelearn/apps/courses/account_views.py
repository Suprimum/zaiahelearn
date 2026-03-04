from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import TeacherApplicationForm, StudentSignupForm, TeacherForm
from .models import TeacherApplication, UserProfile, Teacher
from django.contrib import messages
from allauth.account.views import LoginView, SignupView
from django.contrib.auth import get_user_model
from allauth.account.forms import LoginForm





@login_required
def account_delete(request):
    
    try:
        user = get_user_model().objects.get(id=request.user.id)
        user.delete()
        messages.success(request, "Your account has been deleted.")
        print(f"Deleted user: {user.username}")
    except get_user_model().DoesNotExist:
        messages.error(request, "User not found.")
        print("User not found for deletion.")
        return redirect('home')
    

    return render(request, 'account/account_delete.html')

@login_required
def admin_remove_teacher(request, teacher_id):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to perform this action.")

        return HttpResponseForbidden('''
            <h1>403 Forbidden</h1>
            <p>You do not have permission to access this page.</p>
            <a class="btn btn-primary" href="/">Return to Home</a>
                                     ''')

    try:
        teacher = Teacher.objects.get(id=teacher_id)
        teacher.user.delete()  # This will also delete the Teacher profile due to cascading
        messages.success(request, f"Teacher {teacher.user.username} has been removed.")
    except Teacher.DoesNotExist:
        messages.error(request, "Teacher not found.")

    return redirect('courses:admin_dashboard')


class StudentSignupView(SignupView):
    form_class = StudentSignupForm
    template_name = "account/signup.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        # Update user profile with role
        user = self.request.user
        UserProfile.objects.update_or_create(
            user=user,
            defaults={'role': form.cleaned_data['role']}
        )
        
        if form.cleaned_data['role'] == 'teacher':
            messages.info(self.request, "You have signed up as a teacher. Please complete your application to start mentoring.")
            return redirect('courses:teacher_application')
        
        return response
    
    def form_invalid(self, form):
        print("Form errors:", form.errors)  # Debugging line
        return super().form_invalid(form)


class RoleLoginView(LoginView):
    form_class = LoginForm
    template_name = "account/login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        # Additional logic can be added here if needed
        user = self.request.user

        if user.is_superuser:
            return redirect('courses:admin_dashboard')
        elif hasattr(user, 'userprofile') and user.teacher.approved:
            return redirect('courses:teacher_dashboard')
        elif hasattr(user, 'userprofile') and user.userprofile.role == 'student':
            return redirect('courses:dashboard')
        elif hasattr(user, 'teacher') and not user.teacher.approved:
            messages.warning(self.request, "Your teacher application is pending approval. Please wait for confirmation.")
            return redirect('courses:teacher_application')

        else:
            print(f"User {user.username} has no profile or is not approved.")


        return response

    def form_invalid(self, form):
        print("Login form errors:", form.errors)  # Debugging line
        return super().form_invalid(form)
    




@login_required
def teacher_application_entry(request):
    # If user is already a teacher, redirect to dashboard
    if hasattr(request.user, 'teacher') and request.user.teacher.approved:
        messages.info(request, "You are already a teacher. Redirecting to dashboard.")
        return redirect('courses:teacher_dashboard')
    
    # If user has already applied, show application status
    existing_application = TeacherApplication.objects.filter(user=request.user).first()
    if existing_application:
        if existing_application.status == "approved":
            messages.info(request, "Your teacher application has been approved. Redirecting to dashboard.")
            return redirect('courses:teacher_dashboard')
        elif existing_application.status == "pending":
            messages.info(request, "Your teacher application is pending approval. Please wait for confirmation.")
            return render(request, "teacher/application_status.html", {"application": existing_application})
        elif existing_application.status == "rejected":
            messages.info(request, "Your teacher application was rejected. You may contact support for more information.")
            return render(request, "teacher/application_status.html", {"application": existing_application})
    
    else:
        # If no existing application, show the application form
        if request.method == "POST":
            form = TeacherApplicationForm(request.POST)
            if form.is_valid():
                application = form.save(commit=False)
                application.user = request.user
                application.save()
                messages.success(request, "Your teacher application has been submitted and is pending approval.")
                return redirect('courses:teacher_application')
        else:
            form = TeacherApplicationForm()

    return render(request, "teacher/application_form.html", {"form": form})