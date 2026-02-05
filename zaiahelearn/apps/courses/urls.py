from django.urls import path
from . import views


app_name = "courses"


urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("course/<slug:slug>/<int:id>/", views.course_detail, name="course_detail"),
    path("course/<slug:slug>/<int:id>/lesson/<int:lesson_id>/", views.lesson_detail, name="lesson_detail"),
    path("enroll/", views.enroll_courses_page, name="enroll_courses"),
    path("enroll/<int:course_id>/", views.enroll_course, name="enroll_course"),
    path('teacher/lessons/', views.teacher_lessons, name='teacher_dashboard'),
    path('teacher/lesson/new/', views.lesson_editor, name='lesson_create'),
    path('teacher/lesson/<int:lesson_id>/', views.lesson_editor, name='lesson_edit'),
    path('teach/', views.teacher_application_entry, name='teacher_application'),
    path("teacher/lesson/<int:lesson_id>/delete/",views.delete_lesson,name="lesson_delete"),
    path("quiz/lesson/<int:lesson_id>/", views.lesson_quiz, name="lesson_quiz"),

]
