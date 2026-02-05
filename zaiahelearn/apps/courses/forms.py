from django import forms
from .models import Lesson
from .models import TeacherApplication




class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            'course',
            'title',
            'content_html',
            'content_markdown',
            'status'
        ]

        widgets = {
            'content_html': forms.Textarea(attrs={
                'class': 'rich-editor form-control',
                'placeholder': 'Write lesson in HTML...',
                'required': False,
            }),
            'content_markdown': forms.Textarea(attrs={
                'rows': 12,
                'class': 'markdown-editor form-control',
                'placeholder': 'Write lesson in Markdown...',
                'required': False,
            })
        }




class TeacherApplicationForm(forms.ModelForm):
    class Meta:
        model = TeacherApplication
        fields = [
            'full_name',
            'subject',
            'experience_years',
            'motivation'
        ]
        widgets = {
            'motivation': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Why do you want to teach on ZaiaheLearn?'
            })
        }
