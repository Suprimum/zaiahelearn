from django.shortcuts import redirect
from django.contrib import messages
import markdown
from .models import Choice, Question, QuestionBank, Quiz, AIQuiz, Purchase

from zaiahelearn.ai.main import ai_generate_questions
from django.contrib.contenttypes.models import ContentType



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



def generate_quiz_with_ai(payment, user):

    lesson = payment.lesson

    # call OpenAI or your LLM
    questions = ai_generate_questions(lesson.content)

    quiz = Quiz.objects.create(
        lesson=lesson,
        title=f"AI Quiz - {lesson.title}",
        is_ai_generated=True
    )

    for q in questions:
        question = Question.objects.create(
            quiz=quiz,
            text=q["question"]
        )

        for choice in q["choices"]:
            Choice.objects.create(
                question=question,
                text=choice["text"],
                is_correct=choice["correct"]
            )

    AIQuiz.objects.create(
        lesson=lesson,
        user=user,
        source_payment=payment
    )

    return quiz

   



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
        if not request.user.is_authenticated:
            messages.error(request,"You must create an account to access course lessons ")
            return redirect("account_signup")
        if not hasattr(request.user, 'userprofile') or not request.user.userprofile.role == 'student':
            messages.error(request,"Student account is required")
            print ("your role:  ",request.user.userprofile.role)
            return redirect("account_signup")
        
        return view_func(request, *args, **kwargs)
    return wrapper

def teacher_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'userprofile') or not request.user.userprofile.role == 'teacher':
            messages.error(request, "Teacher access required.")
            return redirect('courses:dashboard')
        if not request.user.teacher.approved:
            messages.warning(request, "Your teacher account is awaiting approval.")
            return redirect('courses:teacher_application')
        return view_func(request, *args, **kwargs)
    return wrapper


def save_question(user,lesson,question_contents,quiz,option_A,option_B,option_C,option_D,correct_choices,difficulties):
    for index, content in enumerate(question_contents):

        if not content.strip():
            continue  # Skip empty questions

        question = Question.objects.create(
                quiz=quiz,
                content_html=content,
                correct_choice=correct_choices[index],
                order=index,
                difficulty = difficulties[index],
        )
        question.save()

        question_bank = QuestionBank.objects.create(
            teacher = user,
            lesson = lesson,
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





