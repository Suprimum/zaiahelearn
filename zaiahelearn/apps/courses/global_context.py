
from .utils import user_has_access  
from django.utils import timezone



def quiz_events(request):
    context = {}

    if request.user.is_authenticated:
        # Get all quizzes the user has access to
        accessible_quizzes = set()
        context['event_quizzes'] = accessible_quizzes

    return context