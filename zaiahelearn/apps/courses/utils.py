from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
import markdown
from .models import Choice, Question, QuestionBank, Purchase

from django.contrib.contenttypes.models import ContentType
from django.http.response import HttpResponseForbidden






def user_has_access(user, obj):
    if not obj.is_paid:
        return True

    ct = ContentType.objects.get_for_model(obj)

    return Purchase.objects.filter(
        student=user,
        content_type=ct,
        object_id=obj.id,
        paid=True
    ).exists()





def render_lesson_content(lesson):
    if lesson.content_html:
        return lesson.content_html
    return markdown.markdown(
        lesson.content_markdown,
        extensions=['fenced_code', 'tables']
    )


def premium_required(view):

    def wrapper(request, *args, **kwargs):
        if not request.user.subscription.active:
            return redirect('pricing')
        return view(request, *args, **kwargs)
    
    return wrapper


def get_embed_pdf(url):

    if not url:
        return None

    # Google Drive share → embed preview
    if "drive.google.com" in url and "/view" in url:
        file_id = url.split("/d/")[1].split("/")[0]
        return f"https://drive.google.com/file/d/{file_id}/preview"

    # Dropbox → raw
    if "dropbox.com" in url:
        return url.replace("?dl=0", "?raw=1")

    return url


def student_required(view_func):
    def wrapper(request,*args,**kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        if not request.user.is_authenticated:
            messages.error(request,"You must create an account to access course lessons ")
            return redirect("account_signup")
        if not hasattr(request.user, 'userprofile'):
            messages.error(request,"Student account is required")
            print ("your role:  ",request.user.userprofile.role)
            return redirect("account_signup")
        
        if request.user.userprofile.role != 'student':
            messages.error(request,"Student account required")
            print ("your role:  ",request.user.userprofile.role)
            return HttpResponseForbidden('''
                <h1>403 Forbidden</h1>
                <p>You do not have permission to access this page. You must have a student account.</p>
                <a class="btn btn-primary" href="/">Return to Home</a>
                ''') 
        
        return view_func(request, *args, **kwargs)
    return wrapper

def teacher_required(view_func):
    def wrapper(request, *args, **kwargs):

        if request.user.is_authenticated and request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        if not hasattr(request.user, 'userprofile') or not request.user.userprofile.role == 'teacher':
            messages.error(request, "Teacher access required.")
            return redirect('courses:dashboard')
        
        if not request.user.teacher.approved:
            messages.warning(request, "Your teacher account is awaiting approval.")
            return redirect('courses:teacher_application')
        return view_func(request, *args, **kwargs)
    return wrapper


def save_question(data,user,quiz,lesson=None,course=None,is_ai_generated=False):

    
    question_contents_html = data.getlist("question_content_html[]")
    correct_choices = data.getlist("correct_choice[]")
    difficulties = data.getlist("difficulty[]")
    level = data.get("level")

    option_A = data.getlist("option_A[]")
    option_B = data.getlist("option_B[]")
    option_C = data.getlist("option_C[]")
    option_D = data.getlist("option_D[]")
    
    for index, content in enumerate(question_contents_html):

        if not content.strip():
            continue  # Skip empty questions

        question = Question.objects.create(
                quiz=quiz,
                content_html=content,
                correct_choice=correct_choices[index],
                order=index,
                level=level,
                difficulty = difficulties[index],
                is_ai_generated = is_ai_generated,
        )
        question.save()

        question_bank = QuestionBank.objects.create(
            teacher = user,
            lesson = lesson,
            course = course,
            level = level,
            question = question,
            difficulty = difficulties[index],
        )

            # Create choices
        Choice.objects.create(
                question=question,
                choice="A",
                answer=option_A[index],
                is_correct = True if correct_choices[index] == "A" else False
        ).save()
        Choice.objects.create(
                question=question,
                choice="B",
                answer=option_B[index],
                is_correct = True if correct_choices[index] == "B" else False
        ).save()
        Choice.objects.create(
                question=question,
                choice="C",
                answer=option_C[index],
                is_correct = True if correct_choices[index] == "C" else False
        ).save()
        Choice.objects.create(
                question=question,
                choice="D",
                answer=option_D[index],
                is_correct = True if correct_choices[index] == "D" else False
        ).save()






