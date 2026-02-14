from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Course, Lesson, LessonProgress
from .forms import  ContactForm
from .utils import  teacher_required
from django.contrib import messages

from .lesson_quiz_views import *
from .account_views import *
from .course_views import *



from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
import json






@login_required
@require_POST
def save_lesson_progress(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)

    data = request.POST
    
    percent = float(data.get("percent", 0))
    scroll_position = int(data.get("scroll", 0))

    progress, created = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )

    print ('progress data: ',data)

    progress.progress_percent = percent
    progress.last_scroll_position = scroll_position

    # Auto mark completed at 90%
    if percent >= 90 and not progress.completed:
        progress.completed = True
        progress.completed_at = timezone.now()

    progress.save()

    return JsonResponse({"status": "success"})



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
@require_POST
def reset_lesson_progress(request, lesson_id):
    #data = json.loads(request.body)

    LessonProgress.objects.filter(
        user=request.user,
        lesson_id=int(lesson_id)
    ).update(progress_percent=0, last_scroll_position=0)

    return JsonResponse({"status": "reset"})


@login_required
def dashboard(request):
    courses = Course.objects.all()  # later: filter enrolled

    enrolled_courses = Course.objects.filter(
        enrollment__user=request.user
    )

    completed_lessons = LessonProgress.objects.filter(
        user=request.user,
        completed=True
    )

    quizzes_taken = LessonQuizAttempt.objects.filter(
        user=request.user,
        completed_at__isnull=False
    )

    total_lessons = Lesson.objects.filter(
        course__in=enrolled_courses
    ).count()

    completed_count = completed_lessons.count()

    available_courses = Course.objects.exclude(
        enrollment__user=request.user
    )

    overall_progress = 0
    if total_lessons > 0:
        overall_progress = round((completed_count / total_lessons) * 100, 1)

    popular_lessons = {
        str(course.id): Lesson.objects.filter(course=course)
                                  .order_by('-views')[:3]
        for course in enrolled_courses
    }

    return render(request, "dashboard/profile.html", {
        "courses": courses,
        "courses_count": enrolled_courses.count(),
        "lessons_completed": LessonProgress.objects.filter(user=request.user, completed=True).count(),
        "quizzes_taken": quizzes_taken.count(),
        "enrolled_courses": enrolled_courses,
        "available_courses": available_courses,
        "total_lessons": total_lessons,
        "overall_progress": overall_progress,
        "popular_lessons": popular_lessons,
    })







