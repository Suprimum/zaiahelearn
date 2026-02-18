from django import forms
from .models import Lesson, TeacherApplication, ContactMessage, Quiz, Question, Teacher, Video, PDFResource
from allauth.account.forms import SignupForm





class PDFResourceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Apply bootstrap classes to all default fields
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    class Meta:
        model = PDFResource
        fields = ["course","title", "file", "external_url"]

        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "external_url": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "Paste external PDF link"
            })
        }


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        exclude = ('lesson','created_at','updated_at')
        widgets = {
            'title': forms.TextInput(attrs={
                "class": 'form-control',
                "placeholder": "video title",
            }),

            'video_url': forms.TextInput(attrs={
                "class": 'form-control',
                "placeholder": "video url"
            }),

            'description':forms.Textarea(attrs={
                "rows": 5,
                'class': "form-control ",
                "placeholder": "video description",
                "required": False,
            }),
        }



class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        exclude = ('created_at','lesson')
        widgets = {
            'title': forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Quiz Title"
            }),
            'description':forms.Textarea(attrs={
                "rows": 5,
                'class': "form-control ",
                "placeholder": "Quiz instructions/description in rich-text format",
                "required": False,
            }),

        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        exclude = ['quiz','bank_question','order']
        widgets = {
            'content_html': forms.Textarea(attrs={
                'rows': 15,
                'class': 'rich-editor form-control',
                'placeholder': 'Write lesson in HTML...',
                'required': False,
            }),
            'content_markdown': forms.Textarea(attrs={
                'rows': 12,
                'class': 'markdown-editor form-control',
                'placeholder': 'Write lesson in Markdown...',
                'required': False,
            }),
            'correct_choice': forms.TextInput(attrs={
                'class': "form-control",
            })
        }
        



class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5
            }),
        }


class StudentSignupForm(SignupForm):
    username = forms.CharField(
        max_length=100,
        label="Username",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "John"
        })
    )

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "you@example.com"
        })
    )
    
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your password"
        })
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Confirm your password"
        })
    )

    role = forms.ChoiceField(
        choices=[('student', 'Student'), ('teacher', 'Teacher')],
        label="I want to sign up as a",
        widget=forms.Select(attrs={
            "class": "form-select"
        })
    )


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Apply bootstrap classes to all default fields
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def save(self, request):
        user = super().save(request)
        user.username = self.cleaned_data["username"]
        user.save()
        return user
    


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



class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        exclude = ['user','approved']
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': 'Tell us about yourself'
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


