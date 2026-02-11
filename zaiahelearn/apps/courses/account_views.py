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
        if hasattr(user, 'userprofile') and user.teacher.approved:
            print(f"User {user.username} has role: {user.userprofile.role}")
            return redirect('courses:teacher_dashboard')
        elif hasattr(user, 'userprofile') and user.userprofile.role == 'student':
            print(f"User {user.username} has role: {user.userprofile.role}")
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
    # Already a teacher
    if hasattr(request.user, 'teacher') and request.user.teacher_application.status == 'approved':
        messages.info(request, "You are already an approved teacher.")
        return redirect('courses:teacher_dashboard')

    # Already applied
    if TeacherApplication.objects.filter(user=request.user).exists():
        application = TeacherApplication.objects.get(user=request.user)

        try:
            request.user.teacher
            return render(request, 'teacher/application_status.html', {
                'application': application
        })
        except Exception as e:
            teacher_form = TeacherForm(request.POST or None)

            if request.method == "POST":
                if teacher_form.is_valid():
                    teacher = teacher_form.save(commit=False)
                    teacher.user = request.user
                    teacher.approved = True
                    teacher.save()

                    return render(request, 'teacher/application_status.html', {
                        'application': application
                    })
            else:
            
                return render(request, 'teacher/application_status.html', {
                    'application': application,
                    'form': teacher_form,
                })
   
    # New application
    form = TeacherApplicationForm(request.POST or None)

    if form.is_valid():
        app = form.save(commit=False)

        if not hasattr(request.user,'userprofile'):
            UserProfile.objects.update_or_create(
            user=request.user,
            defaults={'role': 'teacher'}
            )
        
        app.user = request.user
        app.save()
        messages.success(request, "Application submitted successfully!")

        return redirect('courses:teacher_application')

    return render(request, 'teacher/application_form.html', {
        'form': form
    })
