from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import (
            Course, Lesson, LessonProgress,
            AIQuiz, PDFResource, Purchase,
            Video, Classroom, ClassroomMember,
            ClassroomFile
        )
from .forms import  ContactForm, ClassroomForm
from .utils import  teacher_required, generate_quiz_with_ai
from django.contrib import messages


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.contenttypes.models import ContentType


import requests, json
from django.conf import settings
from django.db.models import Sum

from .lesson_quiz_views import *
from .account_views import *
from .course_views import *








@login_required
def start_payment(request, model_name, object_id):

    MODEL_MAP = {
        "pdf": PDFResource,
        "video": Video,
        "quiz": AIQuiz,
    }

    model = MODEL_MAP.get(model_name)
    if not model:
        return JsonResponse({"error": "Invalid resource"}, status=400)

    obj = get_object_or_404(model, id=object_id)

    if not obj.is_paid:
        return JsonResponse({"error": "Item is free"}, status=400)

    content_type = ContentType.objects.get_for_model(obj)

    purchase, _ = Purchase.objects.get_or_create(
        student=request.user,
        content_type=content_type,
        object_id=obj.id,
        defaults={"amount": obj.price}
    )

    phone = request.POST.get("phone")

    payload = {
        "amount": str(obj.price),
        "currency": "XAF",
        "from": phone,
        "description": f"Payment for {obj}",
        "external_reference": str(purchase.id),
    }

    headers = {
        "Authorization": f"Token {settings.CAMPAY_API_KEY}"
    }

    response = requests.post(
        "https://demo.campay.net/api/collect/",
        json=payload,
        headers=headers
    )

    data = response.json()

    purchase.campay_reference = data.get("reference")
    purchase.external_reference = str(purchase.id)
    purchase.save()

    return JsonResponse(data)


@csrf_exempt
def campay_webhook(request):

    data = json.loads(request.body)

    reference = data.get("reference")
    status = data.get("status")
    external_reference = data.get("external_reference")

    purchase = Purchase.objects.filter(
        external_reference=external_reference
    ).first()

    if purchase and status == "SUCCESSFUL":
        purchase.paid = True
        purchase.save()

    return JsonResponse({"status": "ok"})




def homepage(request):
    ol_courses = Course.objects.filter(level='O-Level')
    al_courses = Course.objects.filter(level='A-Level')

    context = {
        'ol_courses': ol_courses,
        'al_courses': al_courses
    }

    return render(request,'base.html',context)





@login_required
def payment_verify(request):

    ref = request.GET.get("tx_ref")
    payment = get_object_or_404(Purchase,external_reference=ref)

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
def teacher_dashboard(request):
    lessons = Lesson.objects.filter(author=request.user).order_by('-updated_at')
    classrooms = Classroom.objects.filter(teacher=request.user)

    if lessons:
        courses = (Course.objects.in_bulk(set(lessons.values_list('course',flat=True)))).items()
    
    context = {
        'lessons': lessons,
        'classrooms': classrooms,
        'courses': courses
    }

    return render(request, 'teacher/teacher_dashboard.html', context)


@login_required
@teacher_required
def classroom_list(request):
    teacher = request.user
    classrooms = teacher.created_classrooms.all()

    context = {
        "classrooms": classrooms,
    }

    return render(request,"chatroom/chatroom_list.html",context)

@login_required
@teacher_required
def classroom_create(request):
    if request.method == "POST":
        form = ClassroomForm(request.POST)
        if form.is_valid():
            classroom = form.save(commit=False)
            classroom.teacher = request.user
            classroom.save()
            return redirect('courses:teacher_dashboard')
    else:
        form = ClassroomForm()

    return render(request, "teacher/classroom_create.html", {"form": form})



@login_required
@teacher_required
def approve_student(request, classroom_id, member_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    member = get_object_or_404(ClassroomMember, id=member_id, classroom=classroom)
    member.approved = True
    member.save()

    return redirect('courses:teacher_dashboard')


def classroom_chat(request, classroom_id):
    class_room = get_object_or_404(Classroom,id=classroom_id)

    if class_room:
        context = {
            'classroom':class_room,
        }
        return render(request,'chatroom/chatroom.html',context)
    

@login_required
@teacher_required
def start_class(request, classroom_id):
    room = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    room.is_live = True
    room.save()

    # Notify students via Channels
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"classroom_{room.id}",
        {
            "type": "class_started",
            "message": f"{room.name} is now live!",
        }
    )

    return redirect("classroom_detail", room.id)


@login_required
def upload_class_file(request, room_id):
    room = get_object_or_404(Classroom, id=room_id)

    if request.method == "POST":
        ClassroomFile.objects.create(
            classroom=room,
            uploaded_by=request.user,
            file=request.FILES["file"]
        )
        return redirect("classroom_detail", room.id)



@login_required
@student_required
def student_dashboard(request):
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
        overall_progress = LessonProgress.objects.filter(
            user=request.user,
            completed=True
        ).aggregate(
            progress=Sum("progress_percent")
        )["progress"] 

        if overall_progress is None:
            overall_progress = 0
        else:
            overall_progress = round(overall_progress / total_lessons, 1)

    popular_lessons = {
        str(course.id): Lesson.objects.filter(course=course)
                                  .order_by('-views')[:3]
        for course in enrolled_courses
    }

    classrooms = Classroom.objects.filter(is_active=True)#.exclude(members__student=request.user)
    requests_sent = ClassroomMember.objects.filter(student=request.user)
    joined_classrooms = ClassroomMember.objects.filter(student=request.user, approved=True)

    context = {
        "classrooms": classrooms,
        "requests_sent": requests_sent,
        "joined_classrooms": joined_classrooms,
        "courses": courses,
        "courses_count": enrolled_courses.count(),
        "lessons_completed": LessonProgress.objects.filter(user=request.user, completed=True).count(),
        "quizzes_taken": quizzes_taken.count(),
        "enrolled_courses": enrolled_courses,
        "available_courses": available_courses,
        "total_lessons": total_lessons,
        "overall_progress": round(overall_progress,1),
        "popular_lessons": popular_lessons,
    }

    return render(request, "dashboard/profile.html", context)




@login_required
@student_required
def join_classroom(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    ClassroomMember.objects.get_or_create(student=request.user, classroom=classroom)
    return redirect('courses:dashboard')



@login_required
@teacher_required
def join_classroom_request_list(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    pending_requests = classroom.members.filter(approved=False)

    context = {
        'classroom': classroom,
        'pending_requests': pending_requests,
    }

    return render(request,'teacher/classroom_join_request_list.html',context)




