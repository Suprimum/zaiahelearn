from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Lesson, Quiz, Question, LessonQuizAttempt, QuestionBank, Choice, AIQuiz
from django.utils import timezone
from .forms import QuizForm
from .utils import teacher_required, save_question, student_required
from django.contrib import messages
from django.db.models import Avg, Count, Q
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator

from collections import Counter






@login_required
@student_required
def lesson_quiz_page(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)

    quizzes = (
        Quiz.objects
        .filter(lesson=lesson, is_published=True)
        .annotate(question_count=Count("questions"))
        .order_by("-created_at")
    )

    attempts = LessonQuizAttempt.objects.filter(
        user=request.user,
        quiz__lesson=lesson
    ).order_by("completed_at")


    # Map quiz_id -> latest attempt
    attempt_map = {}
    for attempt in attempts:
        if attempt.quiz_id not in attempt_map:
            attempt_map[str(attempt.quiz_id)] = attempt


    return render(request, "courses/student/lesson_quiz_page.html", {
        "lesson": lesson,
        "quizzes": quizzes,
        "attempt_map": attempt_map,
    })




@login_required
@teacher_required
def question_partial(request, pk):
    question = get_object_or_404(QuestionBank, pk=pk, teacher=request.user)
    return render(request, "courses/partials/question_form.html", {
        "question": question
    })




@login_required
@teacher_required
def question_empty_partial(request):
    return render(request, "courses/partials/question_form.html")





@login_required
@teacher_required
def quiz_attempts(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    attempts = LessonQuizAttempt.objects.filter(
        quiz=quiz,
        user=request.user,
    ).select_related("user").order_by("-started_at")

    stats = attempts.aggregate(
        avg_score=Avg("score"),
        total_attempts=Count("id"),
        pass_count=Count("id",filter=Q(score__gte=(quiz.pass_score * attempts.first().total / 100))),
    )

    stats["pass_rate"] = (stats["pass_count"]/stats["total_attempts"]*100) if stats["total_attempts"] else 0
    
    # ✅ TOP PERFORMER
    top_attempt = attempts.order_by("-score").first()

    # ✅ SCORE DISTRIBUTION
    distribution = {
        "0-39": 0,
        "40-59": 0,
        "60-79": 0,
        "80-100": 0,
    }

    for a in attempts:
        pct = (a.score / a.total) * 100 if a.total else 0
        if pct < 40:
            distribution["0-39"] += 1
        elif pct < 60:
            distribution["40-59"] += 1
        elif pct < 80:
            distribution["60-79"] += 1
        else:
            distribution["80-100"] += 1

    # ✅ QUESTION DIFFICULTY ANALYSIS
    difficulty_counter = Counter()

    for attempt in attempts:
        if not attempt.answers: continue
        for qid, chosen in attempt.answers.items():
            question = quiz.questions.filter(id=qid).first()
            if not question:
                continue
            correct = question.choices.filter(is_correct=True).first()
            if correct and chosen != correct.choice:
                difficulty_counter[str(question)] += 1

    hardest_questions = difficulty_counter.most_common(5)

    context = {
        "quiz": quiz,
        "attempts": attempts,
        "stats": stats,
        "top_attempt": top_attempt,
        "distribution": distribution,
        "hardest_questions": hardest_questions,
    }

    return render(request, "courses/quiz_attempts.html", context)


@login_required
def quiz_preview(request, quiz_id):
    quiz = get_object_or_404(
        Quiz.objects.prefetch_related("questions__choices"),
        id=quiz_id
    )

    return render(request, "courses/quiz_preview.html", {
        "quiz": quiz
    })


@login_required
def quiz_add_from_bank(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    questions = QuestionBank.objects.filter(
        teacher=request.user
    )

    
    difficulty = request.GET.get("difficulty")
    topic = request.GET.get("topic")

    
    if difficulty:
        questions = questions.filter(difficulty=difficulty)

    if topic:
        questions = questions.filter(question__content_html__icontains=topic)

    
    paginator = Paginator(questions, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    if request.method == "POST":
        ids = request.POST.getlist("question_ids")

        for q in QuestionBank.objects.filter(id__in=ids):
            new_question = Question.objects.create(
                quiz=quiz,
                content_html=q.question.content_html,
                content_markdown=q.question.content_markdown,
                difficulty=q.difficulty
            )
            
            options = Choice.objects.filter(question=q.question)
            for opt in options:
                opt.id = None
                opt.pk = None
                opt.question = new_question
                opt.save()


        return redirect("courses:lesson_quiz_list", quiz.lesson.id)

    return render(request, "teacher/quiz_add_from_bank.html", {
        "quiz": quiz,
        "questions": questions,
        "page_obj": page_obj,
    })


@login_required
@teacher_required
def lesson_quiz_list(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)

    quizzes = (
        Quiz.objects
        .filter(lesson=lesson)
        .prefetch_related("questions")
        .order_by("-created_at")
    )

    return render(request, "courses/lesson_quiz_list.html", {
        "lesson": lesson,
        "quizzes": quizzes
    })


@login_required
@teacher_required
def lesson_quiz(request, lesson_id, quiz_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    quiz = get_object_or_404(Quiz, lesson=lesson, id=quiz_id)

    return render(request, "courses/lesson_quiz.html", {
        "lesson": lesson,
        "quiz": quiz
    })


@login_required
@teacher_required
def quiz_create_edit(request, lesson_id, quiz_id=None):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    quiz = None
    form = None
    #instantiate a new ai quiz object
    ai_quiz = AIQuiz.objects.create(lesson=lesson,user=request.user)

    if quiz_id: #edit quiz
        quiz = get_object_or_404(Quiz, id=quiz_id, lesson=lesson)

    if request.method == "POST":
        print (request.POST)
        form = QuizForm(request.POST, instance=quiz)

        if form.is_valid():
            print(form.cleaned_data)
            quiz = form.save(commit=False)
            quiz.lesson = lesson

            quiz.save()

            print(quiz)
            # 🔥 Clear old questions if editing
            if quiz_id:
                quiz.questions.all().delete()

            # -----------------------------
            # HANDLE QUESTIONS
            # -----------------------------
            question_contents_html = request.POST.getlist("question_content_html[]")
            question_contents_markdown = request.POST.getlist("question_content_markdown[]")
            correct_choices = request.POST.getlist("correct_choice[]")
            difficulties = request.POST.getlist("difficulty[]")

            option_A = request.POST.getlist("option_A[]")
            option_B = request.POST.getlist("option_B[]")
            option_C = request.POST.getlist("option_C[]")
            option_D = request.POST.getlist("option_D[]")

            if question_contents_html:
                save_question(request.user,lesson,question_contents_html,quiz,option_A,option_B,option_C,option_D,correct_choices,difficulties)
                print ('question content html: ',question_contents_html)

            elif question_contents_markdown:
                save_question(question_contents_markdown,quiz,option_A,option_B,option_C,option_D,correct_choices)
                print ('question content markdown: ',question_contents_markdown)

                messages.success(
                    request,
                    "Quiz created successfully!" if not quiz_id else "Quiz updated successfully!"
                )

            return redirect("courses:lesson_quiz_list", lesson.id)

        else:
            print("Form errors:", form.errors)

    else:
        form = QuizForm(instance=quiz)


    questions = quiz.questions.all() if quiz else []

    return render(request, "courses/quiz_form.html", {
        "lesson": lesson,
        "quiz": quiz,
        "ai_quiz":ai_quiz,
        "form": form,
        "questions": questions,
    })


@login_required
@teacher_required
def quiz_delete(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == "POST":
        quiz.delete()
        messages.success(request, "Quiz deleted successfully!")
        return redirect('courses:lesson_quiz_list', lesson_id=quiz.lesson.id)

    return render(request, "teacher/quiz_confirm_delete.html", {
        "quiz": quiz
    })




@login_required
@student_required
def quiz_attempt(request, quiz_id):
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        is_published=True
    )

    questions = quiz.questions.prefetch_related("choices").all()

    # 🔹 Get unfinished attempt (if exists)
    attempt = LessonQuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        completed_at__isnull=True
    ).first()

    # 🔹 If no active attempt, create one
    if not attempt:
        attempt = LessonQuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            lesson=quiz.lesson,   # if you still keep lesson field
            total=questions.count()
        )

    # ========================
    # SUBMIT QUIZ
    # ========================
    if request.method == "POST":
        score = 0
        answers = {}

        for question in questions:
            selected = request.POST.get(str(question.id))
            answers[str(question.id)] = selected or None

            if selected:
                if question.choices.filter(
                    choice=selected,
                    is_correct=True
                ).exists():
                    score += 1

        attempt.answers = answers
        attempt.score = score
        attempt.completed_at = timezone.now()
        attempt.user_attempts += 1

        # Calculate percentage safely
        if attempt.total > 0:
            percentage = (score / attempt.total) * 100
        else:
            percentage = 0

        attempt.passed = percentage >= quiz.pass_score
        attempt.save()

        return redirect("courses:quiz_result", attempt.id)

    # ========================
    # DISPLAY QUIZ
    # ========================
    return render(request, "courses/quiz_attempt.html", {
        "quiz": quiz,
        "questions": questions,
        "attempt": attempt,
    })





@login_required
def quiz_result(request, attempt_id):
    attempt = get_object_or_404(
        LessonQuizAttempt.objects.select_related("quiz", "user")
        .prefetch_related("quiz__questions__choices"),
        id=attempt_id
    )

    # 🔐 Ensure students can only view their own attempts
    if attempt.user != request.user:
        raise PermissionDenied("You are not allowed to view this result.")

    quiz = attempt.quiz
    questions = quiz.questions.prefetch_related("choices")

    for q in questions:
        correct_choice = q.choices.filter(is_correct=True).first()
        q.correct_label = correct_choice.choice if correct_choice else None

    percentage = 0
    if attempt.total > 0:
        percentage = round((attempt.score / attempt.total) * 100, 2)

    context = {
        "attempt": attempt,
        "quiz": quiz,
        "questions": questions,
        "percentage": percentage,
    }

    return render(request, "courses/quiz_result.html", context)
