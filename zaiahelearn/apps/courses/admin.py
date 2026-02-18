from django.contrib import admin
from .models import (
    Course, Lesson, TeacherApplication, 
    Teacher, UserProfile, Quiz, Question, 
    Choice, QuestionBank, LessonQuizAttempt,
    Video, PDFResource
    )



@admin.action(description="Approve selected teacher applications")
def approve_teacher_applications(modeladmin, request, queryset):
    for application in queryset:
        application.status = 'approved'
        application.save()
        teacher, created = Teacher.objects.get_or_create(user=application.user)
        teacher.approved = True
        teacher.save()


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    list_display = ("id", "title", "level")
    search_fields = ("title", "level")

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "course", "status", "author", "created_at", "views")
    search_fields = ("title", "course__title")

@admin.register(TeacherApplication)
class TeacherApplicationAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "submitted_at")
    list_filter = ("status",)
    search_fields = ("user__username", "user__email")
    actions = [approve_teacher_applications]


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("user", "approved")
    list_filter = ("approved",)
    search_fields = ("user__username", "user__email")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title','is_published','created_at','time_limit','pass_score','lesson')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz','content_html','content_markdown')


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['question','choice','answer','is_correct']


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ['lesson','difficulty']

@admin.register(LessonQuizAttempt)
class LessonQuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user','lesson','quiz',]

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['lesson','title','video_url']

    def video_url(self,model):
        return model.title
    


@admin.register(PDFResource)
class PDFResourceAdmin(admin.ModelAdmin):
    list_display = ['course','title','file','external_url']