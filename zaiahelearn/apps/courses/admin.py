from django.contrib import admin
from .models import Course, Lesson, TeacherApplication, Teacher



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


