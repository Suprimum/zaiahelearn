
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Course, Lesson, LessonProgress, Enrollment, Video, PDFResource
from django.utils import timezone
from .forms import LessonForm, VideoForm, PDFResourceForm
from .utils import render_lesson_content, teacher_required, student_required
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
    course = get_object_or_404(Course, slug=slug,id=course_id)

    try:
        has_paid = True if request.user.ai_quiz_payment.status == 'paid' else False
    except Exception as e:
        has_paid = False

    if lesson_id == None:
        lesson = Lesson.objects.filter(course=course).first()
    else:
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    lessons = Lesson.objects.filter(course=course, status='published').order_by('created_at')
    videos = lesson.video_lessons.all()
    enroll_courses = request.user.enrollments.all().select_related('course')

    # Track views
    if lesson.is_published():
        lesson.views += 1
        lesson.save(update_fields=['views'])

        lesson_progress = LessonProgress.objects.filter(
            user=request.user,
            lesson=lesson
        ).first()


    return render(request, "courses/course_detail.html", {
        "course": course,
        "cur_lesson": lesson,
        "lessons": lessons,
        "lesson_content": lesson.content_html or render_lesson_content(lesson) or "Content coming soon...",
        "enrolled_courses": enroll_courses,
        "lesson_progress": lesson_progress,
        "saved_percent": lesson_progress.progress_percent if lesson_progress else 0,
        "saved_scroll": lesson_progress.last_scroll_position if lesson_progress else 0,
        "videos": videos,
        'has_paid':has_paid,
    })


@login_required
def next_lesson(request,slug,course_id,lesson_id):
    try:
        next_l = Lesson.objects.get(id=lesson_id+1)
        return lesson_detail(request,slug,course_id,next_l.id)
    except:
        next_l = Lesson.objects.first()
        return lesson_detail(request,slug,course_id,next_l.id)
    

@login_required
def prev_lesson(request,slug,course_id,lesson_id):
    try:
        prev_l = Lesson.objects.get(id=lesson_id-1)
        return lesson_detail(request,slug,course_id,prev_l.id)
    except:
        prev_l = Lesson.objects.last()
        return lesson_detail(request,slug,course_id,prev_l.id)


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
def ai_lesson_quiz(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)

    # later you plug AI generator here
    return render(request,"courses/ai_quiz_loading.html",{"lesson":lesson})


@login_required
@teacher_required
def pdf_manage(request, lesson_id, pdf_id=None):

    lesson = get_object_or_404(Lesson, id=lesson_id)

    pdf = None
    if pdf_id:
        pdf = get_object_or_404(PDFResource, id=pdf_id, lesson=lesson)

    if request.method == "POST":
        form = PDFResourceForm(request.POST, request.FILES, instance=pdf)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.lesson = lesson
            obj.save()
            return redirect("courses:lesson_detail",
                            lesson.course.slug,
                            lesson.course.id,
                            lesson.id)
    else:
        form = PDFResourceForm(instance=pdf)

    return render(request, "teacher/lesson_pdf_form.html", {
        "form": form,
        "lesson": lesson,
        "pdf": pdf
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




def pdf_list(request):
    pdfs = PDFResource.objects.all().order_by("-uploaded_at")

    context = {
        "pdfs": pdfs,
        "total": pdfs.count(),
    }
    return render(request, "teacher/pdf_list.html", context)



def pdf_preview(request, pk):
    pdf = get_object_or_404(PDFResource, pk=pk)

    return render(request, "teacher/pdf_preview.html", {
        "pdf": pdf
    })