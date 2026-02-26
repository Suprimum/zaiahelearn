from django import template
from zaiahelearn.apps.courses.models import Question, Lesson

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if dictionary:
        return dictionary.get(str(key))
    
    return None

@register.filter
def add_class(field, css):
    existing_classes = field.field.widget.attrs.get('class', '')
    new_classes = f"{existing_classes} {css}".strip()
    
    return field.as_widget(attrs={'class': new_classes})



@register.filter
def choice_answer(question_id, letter):

    question = Question.objects.get(id=question_id)
    print ("question: ",question)
    
    return question.get_choice_answer(letter)



@register.filter
def grade(pct,pass_score):
    pct = int(pct)
    pass_score = int(pass_score)

    if pct > pass_score:
        return "bg-success"
    elif pct == pass_score:
        return "bg-warning"
    else:
        return "bg-danger"
    
@register.filter
def contains(queryset,item):
    return queryset.filter(student=item).exists()

   
@register.filter
def contains_approved(queryset,item):
    return queryset.filter(student=item,approved=True).exists()

@register.filter
def approved(queryset):
    return queryset.filter(approved=True)

@register.filter
def pending(queryset):
    return queryset.filter(approved=False)

@register.filter
def isteacher(user,teacher):
    return True if user == teacher else False