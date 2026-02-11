from django.shortcuts import redirect
from django.contrib import messages
import markdown
from .models import Choice, Question, QuestionBank


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


def teacher_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'teacher'):
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
