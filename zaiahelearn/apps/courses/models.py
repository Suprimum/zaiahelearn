from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User

class Course(models.Model):
    LEVEL_CHOICES = [
        ('O-Level', 'O-Level'),
        ('A-Level', 'A-Level'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    description = models.TextField()


    def __str__(self):
        return self.title



class Lesson(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

    content_html = models.TextField(blank=True)
    content_markdown = models.TextField(blank=True)


    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft'
    )

    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    views = models.PositiveIntegerField(default=0)

    def is_published(self):
        return self.status == 'published'

    def __str__(self):
        return self.title


class LessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'lesson')


class Quiz(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    text = models.TextField()

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

class LessonQuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey("Lesson", on_delete=models.CASCADE)
    questions = models.JSONField()
    user_answers = models.JSONField(null=True, blank=True)
    score = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.lesson}"
    

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=255)



class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user} → {self.course}"



class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
    


class TeacherApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    subject = models.CharField(max_length=100)
    experience_years = models.PositiveIntegerField()
    motivation = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} – {self.status}"
    

class Video(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200)
    url = models.URLField()

class Resource(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='resources/')

'''
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True)
    courses = models.ManyToManyField(Course, related_name='enrolled_users', blank=True)

    def __str__(self):
        return self.user.username
'''