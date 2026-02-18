from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from embed_video.fields import EmbedVideoField
import uuid

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
    lesson = models.ForeignKey(Lesson,on_delete=models.CASCADE,related_name='video_lessons')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    video_url = EmbedVideoField(verbose_name="Video URL",null=True)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.lesson.title} — {self.title}"

    @property
    def has_description(self):
        return bool(self.description.strip()) if self.description else False
    


class AIQuizPayment(models.Model):

    STATUS = (
        ("pending","Pending"),
        ("paid","Paid"),
        ("failed","Failed"),
    )

    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="ai_quiz_payment")
    lesson = models.ForeignKey("Lesson",on_delete=models.CASCADE)

    amount = models.DecimalField(max_digits=6,decimal_places=2)
    reference = models.UUIDField(default=uuid.uuid4, unique=True)

    provider = models.CharField(max_length=50,blank=True)
    status = models.CharField(max_length=10,choices=STATUS,default="pending")

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return f"{self.user} - {self.lesson} - {self.status}"
    
class AIQuiz(models.Model):
    lesson = models.ForeignKey("Lesson",on_delete=models.CASCADE)
    user = models.ForeignKey(User,on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    source_payment = models.OneToOneField(
        AIQuizPayment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

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


class PDFResource(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='resources', null=True)
    author = models.ForeignKey(User,on_delete=models.CASCADE,related_name='resource',null=True)
    title = models.CharField(max_length=200)
    #uploaded pdfs
    file = models.FileField(upload_to='resources/',blank=True,null=True)
    #external pdf
    external_url = models.URLField(blank=True,null=True,help_text="Paste Google Drive, Dropbox, or driect PDF link")

    uploaded_at = models.DateTimeField(auto_now_add=True,db_index=True)

    def has_file(self):
        return bool(self.file or self.external_url)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    


'''
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True)
    courses = models.ManyToManyField(Course, related_name='enrolled_users', blank=True)

    def __str__(self):
        return self.user.username
'''