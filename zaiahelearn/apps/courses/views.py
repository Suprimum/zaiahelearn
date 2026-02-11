from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Course, Lesson, LessonProgress
from .forms import  ContactForm
from .utils import  teacher_required
from django.contrib import messages

from .lesson_quiz_views import *
from .account_views import *
from .course_views import *





def contact_us(request):
    form = ContactForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your message has been sent successfully!")
        return redirect("courses:contact")

    return render(request, "contact_us.html", {"form": form})




@login_required
@teacher_required
def teacher_lessons(request):
    lessons = Lesson.objects.filter(author=request.user).order_by('-updated_at')
    
    return render(request, 'teacher/lesson_list.html', {
        'lessons': lessons
    })



@login_required
def dashboard(request):
    courses = Course.objects.all()  # later: filter enrolled

    enrolled_courses = Course.objects.filter(
        enrollment__user=request.user
    )

    available_courses = Course.objects.exclude(
        enrollment__user=request.user
    )

    popular_lessons = {
        course.id: Lesson.objects.filter(course=course)
                                  .order_by('-views')[:3]
        for course in enrolled_courses
    }

    return render(request, "dashboard/profile.html", {
        "courses": courses,
        "courses_count": enrolled_courses.count(),
        "lessons_completed": LessonProgress.objects.filter(user=request.user, completed=True).count(),
        "quizzes_taken": 0,  # To be implemented
        "enrolled_courses": enrolled_courses,
        "available_courses": available_courses,
        "popular_lessons": popular_lessons,
    })







