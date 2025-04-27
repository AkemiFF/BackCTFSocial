from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from accounts.models import Tag


class Course(models.Model):
    LEVEL_CHOICES = [
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    category = models.CharField(max_length=100)
    duration = models.CharField(max_length=50)  # Ex: "8 semaines"
    prerequisites = models.TextField(blank=True, null=True)
    instructor = models.CharField(max_length=100)
    image = models.ImageField(upload_to='courses/')
    students = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title


class CourseTag(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('course', 'tag')
    
    def __str__(self):
        return f"{self.course.title} - {self.tag.name}"

class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    duration = models.CharField(max_length=50)  # Ex: "2h 30min"
    order = models.IntegerField(default=0)
    points = models.IntegerField(default=10)  # Points gagnés en complétant ce module
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class ContentItem(models.Model):
    CONTENT_TYPES = [
        ('text', 'Texte'),
        ('image', 'Image'),
        ('video', 'Vidéo'),
        ('file', 'Fichier'),
        ('link', 'Lien'),
    ]
    
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='content_items')
    type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.module.title} - {self.get_type_display()} #{self.order}"

class TextContent(models.Model):
    content_item = models.OneToOneField(ContentItem, on_delete=models.CASCADE, related_name='text_content')
    content = models.TextField()
    
    def __str__(self):
        return f"Texte pour {self.content_item}"

class ImageContent(models.Model):
    POSITION_CHOICES = [
        ('left', 'Gauche'),
        ('center', 'Centre'),
        ('right', 'Droite'),
    ]
    
    content_item = models.OneToOneField(ContentItem, on_delete=models.CASCADE, related_name='image_content')
    image = models.ImageField(upload_to='module_images/')
    position = models.CharField(max_length=10, choices=POSITION_CHOICES, default='center')
    
    def __str__(self):
        return f"Image pour {self.content_item}"

class VideoContent(models.Model):
    PLATFORM_CHOICES = [
        ('youtube', 'YouTube'),
        ('vimeo', 'Vimeo'),
        ('local', 'Locale'),
        ('upload', 'Téléchargée'),
    ]
    
    content_item = models.OneToOneField(ContentItem, on_delete=models.CASCADE, related_name='video_content')
    url = models.URLField(blank=True, null=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    video_file = models.FileField(upload_to='module_videos/', blank=True, null=True)
    
    def __str__(self):
        return f"Vidéo pour {self.content_item}"

class FileContent(models.Model):
    content_item = models.OneToOneField(ContentItem, on_delete=models.CASCADE, related_name='file_content')
    file = models.FileField(upload_to='module_files/')
    filename = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.IntegerField(default=0)  # Taille en KB
    
    def __str__(self):
        return f"Fichier pour {self.content_item}"

class LinkContent(models.Model):
    content_item = models.OneToOneField(ContentItem, on_delete=models.CASCADE, related_name='link_content')
    url = models.URLField()
    description = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"Lien pour {self.content_item}"

class QuizQuestion(models.Model):
    QUESTION_TYPES = [
        ('multiple-choice', 'Choix multiple'),
        ('open-ended', 'Question ouverte'),
    ]
    
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='quiz_questions')
    question = models.TextField()
    type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Question {self.order} pour {self.module.title}"

class QuizOption(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Option pour {self.question}"

class UserProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress')  
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    started_at = models.DateTimeField(_('started at'), auto_now_add=True)
    progress = models.IntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'course')
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.progress}%)"

class ModuleCompletion(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='completed_modules')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)
    time_spent = models.IntegerField(default=0)  # Temps passé en secondes
    
    class Meta:
        unique_together = ('user', 'module')
    
    def __str__(self):
        return f"{self.user.username} a complété {self.module.title}"

class QuizAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learn_quiz_attempts'  # <-- Modifier ici
    )    
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    time_spent = models.IntegerField(default=0)  # Temps passé en secondes
    completed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.module.title} ({self.score}/{self.total_questions})"

class QuizAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(QuizOption, on_delete=models.CASCADE, null=True, blank=True)
    open_answer = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Réponse de {self.attempt.user.username} à {self.question}"

class Certification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certifications') 
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    issued_at = models.DateTimeField(auto_now_add=True)
    certificate_id = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return f"Certification de {self.user.username} pour {self.course.title}"

class PointsTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('module_completion', 'Complétion de module'),
        ('quiz_success', 'Réussite de quiz'),
        ('certification', 'Obtention de certification'),
        ('daily_login', 'Connexion quotidienne'),
        ('other', 'Autre'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='points_transactions') 
    points = models.IntegerField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.points} points ({self.get_transaction_type_display()})"