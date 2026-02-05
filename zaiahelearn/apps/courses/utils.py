from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.contrib import messages
import markdown


def render_lesson_content(lesson):
    if lesson.content_html:
        return lesson.content_html
    return markdown.markdown(
        lesson.content_markdown,
        extensions=['fenced_code', 'tables']
    )


def teacher_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


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
            return redirect('courses:teacher_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper



#teacher_group = Group.objects.create(name='Teacher')
#perm = Permission.objects.get(codename='add_lesson')
#teacher_group.permissions.add(perm)
