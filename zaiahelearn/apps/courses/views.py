from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Course, Lesson, LessonProgress, Quiz, Enrollment
from django.utils import timezone
from .forms import LessonForm, TeacherApplicationForm
from .models import TeacherApplication
from .utils import render_lesson_content, teacher_required
from django.contrib.auth.decorators import permission_required
from django.contrib import messages






@login_required
def teacher_application_entry(request):
    # Already a teacher
    if hasattr(request.user, 'teacher') and request.user.teacher.approved:
        messages.info(request, "You are already an approved teacher.")
        return redirect('courses:teacher_dashboard')

    # Already applied
    if TeacherApplication.objects.filter(user=request.user).exists():
        application = TeacherApplication.objects.get(user=request.user)
        return render(request, 'teacher/application_status.html', {
            'application': application
        })

    # New application
    form = TeacherApplicationForm(request.POST or None)

    if form.is_valid():
        app = form.save(commit=False)
        app.user = request.user
        app.save()
        messages.success(request, "Application submitted successfully!")
        return redirect('courses:teacher_application')

    return render(request, 'teacher/application_form.html', {
        'form': form
    })

@login_required
@teacher_required
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, author=request.user)

    if request.method == "POST":
        lesson.delete()
        messages.success(request, "Lesson deleted successfully.")
        return redirect("courses:teacher_dashboard")

    return redirect("courses:lesson_edit", lesson_id=lesson.id)

@login_required
@teacher_required
def lesson_editor(request, lesson_id=None):
    lesson = get_object_or_404(Lesson, id=lesson_id) if lesson_id else None

    form = LessonForm(request.POST or None, instance=lesson)

    if form.is_valid():
        lesson = form.save(commit=False)
        lesson.author = request.user
        lesson.save()
        return redirect('courses:teacher_dashboard')

    return render(request, 'teacher/lesson_editor.html', {
        'form': form,
        'lesson': lesson
    })


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

def lesson_detail(request, slug, id, lesson_id):
    course = get_object_or_404(Course, slug=slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    lessons = Lesson.objects.filter(course=course, status='published').order_by('created_at')
    enroll_courses = request.user.enrollments.all().select_related('course')

    # Track views
    if lesson.is_published():
        lesson.views += 1
        lesson.save(update_fields=['views'])

    return render(request, "courses/course_detail.html", {
        "course": course,
        "cur_lesson": lesson,
        "lessons": lessons,
        "lesson_content": lesson.content_html or render_lesson_content(lesson) or "Content coming soon...",
        "enrolled_courses": enroll_courses,
    })

def course_detail(request, slug, id):

    course = get_object_or_404(Course, slug=slug)
    lessons = Lesson.objects.filter(course=course)
    enroll_courses = request.user.enrollments.all().select_related('course')

    lesson = lessons.first()  # Show first lesson by default
    if lesson:
        lesson.views += 1
        lesson.save(update_fields=['views'])

    return render(request, "courses/course_detail.html", {
        "course": course,
        "lessons": lessons,
        "cur_lesson": lesson,
        "lesson_content": lesson.content_html or render_lesson_content(lesson) or "Content coming soon...",
        "enrolled_courses": enroll_courses,
    })


def complete_lesson(request, lesson_id):

    progress, _ = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson_id=lesson_id
    )

    progress.completed = True
    progress.completed_at = timezone.now()
    progress.save()

@login_required
def lesson_quiz(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    quiz = get_object_or_404(Quiz, lesson=lesson)

    return render(request, "courses/lesson_quiz.html", {
        "lesson": lesson,
        "quiz": quiz
    })

def submit_quiz(request, quiz_id):

    score = 0
    quiz = Quiz.objects.get(id=quiz_id)

    for q in quiz.question_set.all():
        selected = request.POST.get(str(q.id))

        if q.choice_set.filter(id=selected, is_correct=True).exists():
            score += 1


@login_required
def enroll_courses_page(request):
    courses = Course.objects.all()

    enrolled_course_ids = Enrollment.objects.filter(
        user=request.user
    ).values_list('course_id', flat=True)

    return render(request, "courses/enroll_courses.html", {
        "courses": courses,
        "enrolled_course_ids": enrolled_course_ids
    })


@login_required
def enroll_course(request, course_id):

    course = Course.objects.get(id=course_id)

    Enrollment.objects.get_or_create(
        user=request.user,
        course=course
    )
    return redirect('courses:dashboard')