from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Lesson, Quiz, Question, LessonQuizAttempt, QuestionBank, Choice, AIQuiz, Course
from django.utils import timezone
from .forms import QuizForm
from .utils import teacher_required, save_question, student_required, generate_quiz_with_ai
from django.contrib import messages
from django.db.models import Avg, Count, Q
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator

from collections import Counter

from zaiahelearn.ai.claude_exam_parser import claude_questions_image_parser
from zaiahelearn.ai.ai_to_formdata import build_question_formdata





@login_required
@student_required
def quiz_page(request, lesson_id=None, course_id=None):
    lesson = None
    quizzes = None
    attempts = None    
    course = None
    if lesson_id:
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

    elif course_id:
        course = get_object_or_404(Course,id=course_id)
        quizzes = (
            Quiz.objects
            .filter(course=course, is_published=True)
            .annotate(question_count=Count("questions"))
            .order_by("-created_at")
        )
        attempts = LessonQuizAttempt.objects.filter(
            user=request.user,
            quiz__course=course
            ).order_by("completed_at")


    # Map quiz_id -> latest attempt
    attempt_map = {}
    for attempt in attempts:
        if attempt.quiz_id not in attempt_map:
            attempt_map[str(attempt.quiz_id)] = attempt


    return render(request, "courses/student/lesson_quiz_page.html", {
        "lesson": lesson,
        "course":course,
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
def upload_exam_image(request, quiz_id):

    if request.method == "POST":
        quiz = get_object_or_404(Quiz, id=quiz_id)
        image = request.FILES.get("image")

        ai_questions = claude_questions_image_parser(image)
        print (ai_questions)
        # 🔹 Convert AI output to QueryDict
        form_data = build_question_formdata(ai_questions)

        print (form_data)

        # 🔹 Save using your existing function
        save_question(
            data=form_data,
            user=request.user,
            quiz=quiz,
            course=quiz.course,
            is_ai_generated=True
        )

        messages.success(request,"AI quiz generated successfully.")

        return redirect("courses:course_quiz_list",quiz.course.slug, quiz.course.id)

    context = {}

    return render(request,"teacher/upload_exam_image.html",context)

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

    # Apply search filter
    difficulty = request.GET.get("difficulty")
    topic = request.GET.get("topic")
    level = request.GET.get("level")
    
    if difficulty:
        questions = questions.filter(difficulty=difficulty)

    if topic:
        questions = questions.filter(question__content_html__icontains=topic)
    
    if level:
        questions = questions.filter(level=level)

    
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
                difficulty=q.difficulty,
                level = q.level,
            )
            
            options = Choice.objects.filter(question=q.question)
            for opt in options:
                opt.id = None
                opt.pk = None
                opt.question = new_question
                opt.save()


        return redirect("courses:lesson_quiz_list", quiz.lesson.id) if quiz.lesson else redirect("courses:course_quiz_list", quiz.course.slug, quiz.course.id)

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


'''
@login_required
@teacher_required
def quiz_builder(request, quiz_id):

    quiz = get_object_or_404(Quiz,id=quiz_id)

    if request.method == "POST":
        save_question(request.POST,request.user,quiz,course=quiz.course)

        return redirect("courses:course_quiz_list", quiz.course.slug, quiz.course.id)

    questions = quiz.questions.all()

    return render(request,"courses/quiz_builder.html",{
        "quiz":quiz,
        "questions":questions
    })
'''



@login_required
@teacher_required
def course_quiz_create(request,course_id):

    course = get_object_or_404(Course, id=course_id)

    if request.method == "POST":

        print (request.POST)

        mode = request.POST.get("mode")

        quiz = Quiz.objects.create(
            course=course,
            is_course_quiz=True,
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            time_limit=request.POST.get("time_limit", 10),
            pass_score=request.POST.get("pass_score", 50),
            level = request.POST.get("level"),
        )

        # -------- MANUAL MODE ----------
        if mode == "manual":
            return redirect("courses:course_quiz_builder", course.id, quiz.id)

        # -------- QUESTION BANK MODE ----------
        if mode == "bank":
            difficulty = request.POST.get("difficulty")
            amount = int(request.POST.get("amount", 10))

            return redirect("courses:quiz_add_from_bank", quiz.id)

        # -------- AI MODE ----------
        if mode == "ai":
            topic = request.POST.get("topic")
            amount = int(request.POST.get("amount", 5))

            return redirect("courses:upload_exam_question", quiz.id)

    return render(request,"courses/course_quiz_create.html",{
        "course":course
    })


@login_required
@teacher_required
def quiz_create_edit(request,course_id=None, lesson_id=None, quiz_id=None):
    if lesson_id: #lesson wide quiz
        lesson = get_object_or_404(Lesson, id=lesson_id)
    else:
        lesson = None

    if course_id:#course wide quiz
        course = get_object_or_404(Course,id=course_id)
    else:
        course = None

    quiz = None
    form = None

    #instantiate a new ai quiz object
    #ai_quiz = AIQuiz.objects.create(lesson=lesson,user=request.user)

    if quiz_id: #edit quiz
        quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == "POST":
        form = QuizForm(request.POST, instance=quiz)

        if form.is_valid():
            quiz = form.save(commit=False)
            if lesson:
                quiz.lesson = lesson
            elif course:
                quiz.course = course

            print(form.cleaned_data['level'],' fl-vs-ql ',quiz.level)
            quiz.save()

            # 🔥 Clear old questions if editing
            if quiz_id:
                quiz.questions.all().delete()

            # -----------------------------
            # HANDLE QUESTIONS
            # -----------------------------
            save_question(request.POST,request.user,quiz,lesson=lesson,course=course)
            messages.success(
                request,
                "Quiz created successfully!" if not quiz_id else "Quiz updated successfully!"
            )

            if course_id:
                print ('to course qiz: ')
                return redirect("courses:course_quiz_list", course.slug, course.id)
            elif lesson_id:
                print ('to lesson quiz: ')
                return redirect("courses:lesson_quiz_list", lesson.id)

        else:
            print("Form errors:", form.errors)

    else:
        form = QuizForm(instance=quiz)


    questions = quiz.questions.all() if quiz else []

    return render(request, "courses/quiz_form.html", {
        "lesson": lesson,
        "course": course,
        "quiz": quiz,
        #"ai_quiz":ai_quiz,
        "form": form,
        "questions": questions,
    })


@login_required
@teacher_required
def quiz_delete(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    lesson = None
    course = None
    if quiz.lesson:
        lesson = quiz.lesson
    else:
        course = quiz.course

    if request.method == "POST":
        quiz.delete()
        messages.success(request, "Quiz deleted successfully!")

        return redirect('courses:lesson_quiz_list', lesson.id) if lesson else redirect('courses:course_quiz_list', course.slug, course.id) 

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
        attempt.user_attempts = LessonQuizAttempt.objects.filter(
            user=request.user,
            quiz=quiz
        ).count() + 1  # current attempt included

        # Calculate percentage safely
        if attempt.total > 0:
            percentage = (score / attempt.total) * 100
        else:
            percentage = 0

        attempt.passed = percentage >= quiz.pass_score
        attempt.save()

        print (attempt.user_attempts,' user attempts ')


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
