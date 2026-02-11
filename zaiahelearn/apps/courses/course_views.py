
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Course, Lesson, LessonProgress, Enrollment
from django.utils import timezone
from .forms import LessonForm
from .utils import render_lesson_content, teacher_required
from django.contrib import messages
from django.db.models import Q





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




def complete_lesson(request, lesson_id):

    progress, _ = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson_id=lesson_id
    )

    progress.completed = True
    progress.completed_at = timezone.now()
    progress.save()


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




def course_list(request):
    query = request.GET.get("q", "")

    courses = Course.objects.all()

    if query:
        courses = courses.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
        print(f"Search query: '{query}' - Found {courses.count()} courses")

    return render(request, "courses/explore.html", {
        "courses": courses,
        "query": query
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
