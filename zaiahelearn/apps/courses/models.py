from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from embed_video.fields import EmbedVideoField
import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType






class UserRole(models.TextChoices):
    STUDENT = "student", "Student"
    TEACHER = "teacher", "Teacher"
    ADMIN = "admin", "Admin"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='userprofile')
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STUDENT
    )

    def __str__(self):
        return f"{self.user.username} ({self.role})"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"


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
        return f"{self.title} ({self.level})"
    
    def get_absolute_url(self):
        return reverse("courses:first_lesson_detail",args=(self.slug,self.id,))


class Lesson(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
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
    
    def get_absolute_url(self):
        return reverse('courses:lesson_detail',args=(self.course.slug,self.course.id,self.id))



class LessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)

    progress_percent = models.FloatField(default=0)
    last_scroll_position = models.IntegerField(default=0)

    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'lesson')

    def __str__(self):
        return f"{self.user} - {self.lesson} - ({self.progress_percent}%)"



class Quiz(models.Model):
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="quizzes"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    time_limit = models.PositiveIntegerField(
        help_text="Time limit in minutes", default=10
    )
    pass_score = models.PositiveIntegerField(default=50)
    is_published = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title}-{self.description}-{self.time_limit}-{self.pass_score}"
    

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")

    content_html = models.TextField(blank=True)
    content_markdown = models.TextField(blank=True)
    correct_choice = models.CharField(max_length=1,null=True,blank=True)
    difficulty = models.CharField(
        max_length=20,
        choices=[("easy","Easy"),("medium","Medium"),("hard","Hard")],
        default="medium"
    )
    order = models.PositiveIntegerField(default=0)

    def get_choice_answer(self, letter):
        choice = self.choices.filter(choice=letter).first()
        return choice.answer if choice else ""
    
    def __str__(self):
        return f"{self.content_html}"


class QuestionBank(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson,on_delete=models.CASCADE,related_name='bank', null=True)
    question = models.ForeignKey(Question,on_delete=models.CASCADE,related_name='question_bank',null=True)
    
    difficulty = models.CharField(
        max_length=20,
        choices=[("easy","Easy"),("medium","Medium"),("hard","Hard")],
        default="medium"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lesson.title}"


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    choice = models.CharField(max_length=2,default='A')
    answer = models.CharField(max_length=255,default='')
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.choice}: {self.answer}"
    

class LessonQuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='user_quiz_attempt')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE,null=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE,null=True)

    questions = models.JSONField(null=True)
    answers = models.JSONField(null=True, blank=True)
    passed = models.BooleanField(default=False)

    user_attempts = models.PositiveIntegerField(default=0)

    score = models.IntegerField(default=0)
    total = models.IntegerField(default=0)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def percentage(self):
        if self.total == 0:
            return 0
        return (self.score / self.total) * 100




class Classroom(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_classrooms')
    course = models.ForeignKey(Course, on_delete=models.CASCADE,null=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    live_stream_url = models.URLField(blank=True, null=True, help_text="Link for live stream (Zoom, YouTube, etc.)")
    live_session_active = models.BooleanField(default=False)
    live_session_host = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hosted_sessions"
    )
    
    def __str__(self):
        return f"{self.title} - {self.teacher.username}"
    

class ApprovedMembers(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(approved=True)


class ClassroomMember(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='members')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='classrooms')
    joined_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)  # Teacher must approve
    objects = models.Manager()
    approved_members = ApprovedMembers()

    class Meta:
        unique_together = ('classroom', 'student')


    def __str__(self):
        return f"{self.student.username} in {self.classroom.title}"
    
    


class ClassroomFile(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="files")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to="classroom_files/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

class ClassroomMessage(models.Model):
    classroom_id = models.IntegerField()
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created"]

    def serialize(self, teacher=None):
        return {
            "id": self.id,
            "username": self.sender.username,
            "message": self.message,
            "created": self.created.strftime("%H:%M"),
            "is_teacher": teacher and self.sender == teacher
        }

    def __str__(self):
        return f"{self.sender.username}: {self.message[:20]}"



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
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='teacher')
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

    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='teacher_application')
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
    lesson = models.ForeignKey(
        "Lesson",
        on_delete=models.CASCADE,
        related_name="video_lessons"
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    video_url = EmbedVideoField(verbose_name="Video URL", null=True)

    # 🔒 PAYMENT FIELDS
    is_paid = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.lesson.title} — {self.title}"

    @property
    def has_description(self):
        return bool(self.description.strip()) if self.description else False





class PDFResource(models.Model):
    course = models.ForeignKey(
        "Course",
        on_delete=models.CASCADE,
        related_name="resources",
    )

    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="pdf_resources"
    )

    title = models.CharField(max_length=200)

    # Content
    file = models.FileField(upload_to="resources/", blank=True, null=True)
    external_url = models.URLField(blank=True, null=True)

    # Payment fields
    is_paid = models.BooleanField(default=False)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Set price only if paid resource"
    )

    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def has_file(self):
        return bool(self.file or self.external_url)

    def __str__(self):
        return f"{self.course.title} - {self.title}"




class Purchase(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="purchases"
    )

    # Generic relation (PDF, Video, Quiz, etc)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey("content_type", "object_id")

    amount = models.DecimalField(max_digits=8, decimal_places=2)
    paid = models.BooleanField(default=False)

    campay_reference = models.CharField(max_length=120, blank=True, null=True)
    external_reference = models.CharField(max_length=120, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "content_type", "object_id")

    def __str__(self):
        return f"{self.student} → {self.item}"






class AIQuiz(models.Model):
    lesson = models.ForeignKey("Lesson",on_delete=models.CASCADE)
    user = models.ForeignKey(User,on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    # 🔒 PAYMENT FIELDS
    price = models.PositiveIntegerField(default=250)
    is_paid = models.BooleanField(default=True)

    def __str__(self):
        return f"AI Quiz for {self.lesson}"


class AIQuizQuestion(models.Model):
    quiz = models.ForeignKey(AIQuiz, on_delete=models.CASCADE, related_name="questions")
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1)  # A/B/C/D

'''
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True)
    courses = models.ManyToManyField(Course, related_name='enrolled_users', blank=True)

    def __str__(self):
        return self.user.username
'''