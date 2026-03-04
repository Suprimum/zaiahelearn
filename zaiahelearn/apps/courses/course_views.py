
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import Course, Lesson, LessonProgress, Enrollment, Video, PDFResource
from django.utils import timezone
from .forms import LessonForm, VideoForm, PDFResourceForm
from .utils import render_lesson_content, teacher_required, student_required, user_has_access
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.http import JsonResponse





@login_required
@student_required
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
@student_required
def enroll_course(request, course_id):

    course = Course.objects.get(id=course_id)

    Enrollment.objects.get_or_create(
        user=request.user,
        course=course
    )
    return redirect('courses:dashboard')



@login_required
@student_required
def complete_lesson(request, lesson_id):

    progress, _ = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson_id=lesson_id
    )

    progress.completed = True
    progress.completed_at = timezone.now()
    progress.save()



@login_required
@student_required
def lesson_detail(request, slug, course_id, lesson_id=None):

    course = get_object_or_404(Course, slug=slug, id=course_id)

    # ---------- Lesson selection ----------
    if lesson_id is None:
        lesson = Lesson.objects.filter(course=course).first()
    else:
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

    lessons = Lesson.objects.filter(
        course=course,
        status="published"
    ).order_by("created_at")
    
    videos = lesson.video_lessons.all()
    resources = course.resources.all()

    enroll_courses = request.user.enrollments.select_related("course")

    # ---------- Track lesson views ----------
    lesson_progress = None
    if lesson.is_published:
        lesson.views += 1
        lesson.save(update_fields=["views"])

        lesson_progress = LessonProgress.objects.filter(
            user=request.user,
            lesson=lesson
        ).first()

    # ---------- Paid access logic ----------
    unlocked_pdfs = []
    unlocked_videos = []

    for pdf in resources:
        if user_has_access(request.user, pdf):
            unlocked_pdfs.append(pdf.id)

    for video in videos:
        if user_has_access(request.user, video):
            unlocked_videos.append(video.id)

    context = {
        "course": course,
        "cur_lesson": lesson,
        "lessons": lessons,
        "lesson_content": lesson.render_blocks_to_html() or "Content coming soon...",
        "enrolled_courses": enroll_courses,
        "lesson_progress": lesson_progress,
        "saved_percent": lesson_progress.progress_percent if lesson_progress else 0,
        "saved_scroll": lesson_progress.last_scroll_position if lesson_progress else 0,
        "videos": videos,
        "resources": resources,

        # 🔐 unlocked content IDs for template checks
        "unlocked_pdf_ids": unlocked_pdfs,
        "unlocked_video_ids": unlocked_videos,
    }

    return render(request, "courses/course_detail.html", context)



@login_required
@require_POST
def save_lesson_progress(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)

    data = request.POST
    
    percent = float(data.get("percent", 0))
    scroll_position = float(data.get("scroll", 0))

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

    progress.save(update_fields=[
        "progress_percent",
        "last_scroll_position",
        "completed",
        "completed_at",
        "updated_at"
    ])

    return JsonResponse({"status": "success"})


@login_required
@student_required
@require_POST
def next_prev_lesson(request, lesson_id):

    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course

    # ---- SAVE PROGRESS FIRST ----
    percent = float(request.POST.get("percent", 0))
    scroll = float(request.POST.get("scroll", 0))
    # ---- FIND NEXT/PREV LESSON BY ORDER (NOT ID!) ----
    direction = int(request.POST.get("direction", 1))

    progress, _ = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )
    progress.progress_percent = percent
    progress.last_scroll_position = scroll

    if percent >= 90 and not progress.completed:
        progress.completed = True
        progress.completed_at = timezone.now()

    progress.save()

    lessons = Lesson.objects.filter(
        course=course, 
        status="published"
    ).order_by("created_at")

    lesson_list = list(lessons)

    try:
        index = lesson_list.index(lesson)
    except ValueError:
        index = 0

    if direction == 1:
        new_index = min(index + 1, len(lesson_list) - 1)
    else:
        new_index = max(index - 1, 0)

    target = lesson_list[new_index]

    next_url = reverse(
        "courses:lesson_detail",
        args=[course.slug, course.id, target.id]
    )

    return JsonResponse({
        "status": "ok",
        "url": next_url
    })


@login_required
@require_POST
def reset_lesson_progress(request, lesson_id):

    progress = LessonProgress.objects.get(
        user=request.user,
        lesson=Lesson.objects.get(id=lesson_id)
    )
    progress.progress_percent = 0
    progress.last_scroll_position = 0
    progress.completed = False
    progress.completed_at = None
    progress.save()

    print ('Lesson progress reset for user:', request.user.username, 'lesson_id:', lesson_id)

    return JsonResponse({"status": "reset"})




@login_required
@teacher_required
def course_detail(request,course_id):
    course = Course.objects.get(id=course_id)
    lessons = course.lessons.all()

    context = {
        "course": course,
        "lessons": lessons,
    }

    return render(
        request,
        'teacher/course_detail.html',
        context
    )

@login_required
@teacher_required
def course_quiz_list(request,course_slug,course_id):
    course = get_object_or_404(Course,id=course_id,slug=course_slug)
    quizzes = course.course_quizzes.all()

    context = {
        'course':course,
        'quizzes': quizzes
    }

    return render(
        request,
        'courses/course_quiz_list.html',
        context
        )

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

    if lesson_id:
        lesson = get_object_or_404(
            Lesson,
            id=lesson_id,
            author=request.user
        )
    else:
        lesson = None

    if request.method == "POST":
        form = LessonForm(request.POST, instance=lesson)

        if form.is_valid():
            print ("Form is valid. Saving lesson...",form.cleaned_data)
            lesson = form.save(commit=False)
            lesson.author = request.user
            lesson.save()

            return redirect(
                'courses:course_detail',
                course_id=lesson.course.id
            )
    else:
        form = LessonForm(instance=lesson)

    return render(
        request,
        "teacher/lesson_editor.html",
        {
            "form": form,
            "lesson": lesson,
            "existing_blocks": lesson.content_blocks if lesson else []
        }
    )


@login_required
@teacher_required
def lesson_videos_list(request, lesson_id):
    lesson = get_object_or_404(
        Lesson.objects.select_related("course"),
        id=lesson_id,
        author=request.user   # ensures teacher owns lesson
    )

    videos = lesson.video_lessons.all().order_by("-created_at")

    context = {
        "lesson": lesson,
        "videos": videos,
    }
    return render(request, "teacher/video_lessons_list.html", context)



@login_required
@teacher_required
def lesson_video_create_edit(request, lesson_id, video_id=None):
    """
    Handles BOTH create and edit of lesson videos.
    If video_id is provided → edit mode
    Else → create mode
    """

    lesson = get_object_or_404(Lesson, id=lesson_id, author=request.user)

    # EDIT MODE
    if video_id:
        video = get_object_or_404(Video, id=video_id, lesson=lesson)
    else:
        video = None

    if request.method == "POST":
        form = VideoForm(request.POST, instance=video)

        if form.is_valid():
            video_obj = form.save(commit=False)
            video_obj.lesson = lesson
            video_obj.save()

            if video:
                messages.success(request, "Video updated successfully.")
                print ("Video updated successfully.")
            else:
                messages.success(request, "Video added successfully.")
                print ("Video added successfully.")

            return redirect("courses:lesson_videos_list", lesson_id=lesson.id)

        messages.error(request, "Please correct the errors below.")
        print ("Error: ",form.errors.as_text())

    else:
        form = VideoForm(instance=video)

    context = {
        "form": form,
        "lesson": lesson,
        "video": video,   # lets template know if editing
        "is_edit": bool(video),
    }

    return render(request, "teacher/lesson_video_create.html", context)



@login_required
@teacher_required
def lesson_video_delete(request, lesson_id, video_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, teacher=request.user)
    video = get_object_or_404(Video, id=video_id, lesson=lesson)

    if request.method == "POST":
        video.delete()
        messages.success(request, "Video deleted.")
        return redirect("courses:lesson_video_list", lesson_id=lesson.id)

    return render(request, "teacher/video_confirm_delete.html", {
        "video": video,
        "lesson": lesson
    })







@login_required
@teacher_required
def pdf_create_edit(request, pdf_id=None):
    pdf = None

    if pdf_id:
        pdf = get_object_or_404(PDFResource, id=pdf_id,)

    # DELETE
    if request.method == "POST" and "delete" in request.POST:
        if pdf:
            pdf.delete()
        return redirect(
            "courses:pdf_list",
        )

    # CREATE / UPDATE
    if request.method == "POST":
        form = PDFResourceForm(request.POST, request.FILES, instance=pdf)
        if form.is_valid():
            pdf_resource = form.save(commit=False)
            pdf_resource.author = request.user
            pdf_resource.save()

            return redirect(
                "courses:pdf_list",
            )
    else:
        form = PDFResourceForm(instance=pdf)

    return render(request, "teacher/pdf_form.html", {
        "form": form,
        "pdf": pdf,
        "is_edit": pdf is not None
    })




@login_required
@teacher_required
def pdf_list(request):
    pdfs = PDFResource.objects.all().order_by("-uploaded_at")

    context = {
        "pdfs": pdfs,
        "total": pdfs.count(),
    }
    return render(request, "teacher/pdf_list.html", context)



@login_required
@teacher_required
def pdf_preview(request, pk):
    pdf = get_object_or_404(PDFResource, pk=pk)

    return render(request, "teacher/pdf_preview.html", {
        "pdf": pdf
    })