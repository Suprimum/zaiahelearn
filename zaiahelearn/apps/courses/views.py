from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import Course, Lesson, LessonProgress, AIQuiz
from .forms import  ContactForm
from .utils import  teacher_required, generate_quiz_with_ai
from django.contrib import messages

from .lesson_quiz_views import *
from .account_views import *
from .course_views import *



from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.mail import send_mail



import requests
from django.conf import settings




def homepage(request):
    ol_courses = Course.objects.filter(level='O-Level')
    al_courses = Course.objects.filter(level='A-Level')

    context = {
        'ol_courses': ol_courses,
        'al_courses': al_courses
    }

    return render(request,'base.html',context)


@login_required
def start_flutterwave_payment(request, reference):

    payment = get_object_or_404(AIQuizPayment,reference=reference)

    payload = {
        "tx_ref": str(payment.reference),
        "amount": str(payment.amount),
        "currency": "USD",
        "redirect_url": request.build_absolute_uri(
            reverse("courses:payment_verify")
        ),
        "customer":{
            "email":request.user.email,
            "name":request.user.username
        }
    }

    headers = {
        "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET}",
        "Content-Type":"application/json"
    }

    res = requests.post(
        "https://api.flutterwave.com/v3/payments",
        json=payload,
        headers=headers
    ).json()

    if res['status'] == 'error':
        print (res)
        messages.error(request,res['message'])
        
        return redirect('courses:dashboard')
        
    return redirect(res["data"]["link"])

@login_required
def payment_verify(request):

    ref = request.GET.get("tx_ref")
    payment = get_object_or_404(AIQuizPayment,reference=ref)

    payment.status = "paid"
    payment.paid_at = timezone.now()
    payment.save()

    # 🔥 AUTO GENERATE QUIZ
    quiz = generate_quiz_with_ai(payment, request.user)

    return redirect("courses:view_ai_quiz", quiz.id)


@login_required
def view_ai_quiz(request, quiz_id):

    quiz = get_object_or_404(Quiz,id=quiz_id)

    if not AIQuiz.objects.filter(
        lesson=quiz.lesson,
        user=request.user
    ).exists():
        messages.error(request,"You did not purchase this quiz.")
        return redirect("courses:dashboard")

    return render(request,"student/ai_quiz.html",{"quiz":quiz})


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
        sender_subject = form.cleaned_data['subject']
        sender_name = form.cleaned_data['name']
        sender_message = form.cleaned_data['message']
        sender_email = form.cleaned_data['email']

        recipient_list = ['germaindjango@gmail.com']

        send_mail(
            subject=sender_name+' --> '+sender_subject,
            message= sender_message,
            from_email= sender_email,
            recipient_list=recipient_list
        )
        messages.success(request, "Your message has been sent successfully!")
        return redirect("contact")

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
@student_required
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







