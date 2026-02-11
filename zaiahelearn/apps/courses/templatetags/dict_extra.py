from django import template
from zaiahelearn.apps.courses.models import Question

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
