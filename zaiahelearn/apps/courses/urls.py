from django.urls import path
from . import views


app_name = "courses"


urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("course/<slug:slug>/<int:id>/", views.course_detail, name="course_detail"),
    path("course/<slug:slug>/<int:id>/lesson/<int:lesson_id>/", views.lesson_detail, name="lesson_detail"),
    path("courses/explore/", views.course_list, name="course_list"),
    path("enroll/", views.enroll_courses_page, name="enroll_courses"),
    path("enroll/<int:course_id>/", views.enroll_course, name="enroll_course"),
    path('teacher/lessons/', views.teacher_lessons, name='teacher_dashboard'),
    path('teacher/lesson/new/', views.lesson_editor, name='lesson_create'),
    path('teacher/lesson/<int:lesson_id>/', views.lesson_editor, name='lesson_edit'),
    path('teach/', views.teacher_application_entry, name='teacher_application'),
    path('lesson/<int:lesson_id>/quiz/<int:quiz_id>/detail/', views.lesson_quiz, name='lesson_quiz'),
    path("teacher/lesson/<int:lesson_id>/delete/",views.delete_lesson,name="lesson_delete"),
    path("lesson/quiz/<int:lesson_id>/create/", views.quiz_create_edit, name="quiz_create"),
    path("lesson/<int:lesson_id>/quiz/list/",views.lesson_quiz_list,name="lesson_quiz_list"),
    path("lesson/<int:lesson_id>/quiz/<int:quiz_id>/edit/", views.quiz_create_edit, name="quiz_edit"),
    path("lesson/quiz/<int:quiz_id>/delete/", views.quiz_delete, name="quiz_delete"),
    path("question-partial/<int:pk>/",views.question_partial,name="question_partial"),
    path("quiz/<int:quiz_id>/question/bank/",views.quiz_add_from_bank,name="quiz_add_from_bank"),
    path("quiz/<int:quiz_id>/preview/",views.quiz_preview,name="quiz_preview"),
    path("quiz/<int:quiz_id>/attempts/",views.quiz_attempts,name="quiz_attempts"),
    path("questions/empty/", views.question_empty_partial,name="question_empty_partial"),
    path("lesson/quiz/<int:quiz_id>/attempt/", views.quiz_attempt, name="quiz_attempt"),
    path("lesson/<int:lesson_id>/quizzes/",views.lesson_quiz_page,name="lesson_quiz_page"),
    path("lesson/quiz/attempt/<int:attempt_id>/",views.quiz_result,name="quiz_result"),
    path("lesson/<int:lesson_id>/progress/save/", views.save_lesson_progress, name="save_lesson_progress"),
    path("lesson/<int:lesson_id>/progress/reset/", views.reset_lesson_progress, name="reset_lesson_progress"),
    path("course/<slug:slug>/<int:course_id>/lesson/<int:lesson_id>/next/",views.next_lesson,name="next_lesson"),
    path("course/<slug:slug>/<int:course_id>/lesson/<int:lesson_id>/prev/",views.prev_lesson,name="prev_lesson"),

]
