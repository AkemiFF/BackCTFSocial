import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class LearningPath(models.Model):
    """A structured learning path containing multiple courses."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    slug = models.SlugField(_('slug'), max_length=255, unique=True)
    image = models.ImageField(_('image'), upload_to='learning_paths/', blank=True, null=True)
    difficulty = models.CharField(_('difficulty'), max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ])
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='required_for')
    estimated_hours = models.PositiveIntegerField(_('estimated hours'), default=0)
    is_published = models.BooleanField(_('is published'), default=False)
    is_featured = models.BooleanField(_('is featured'), default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_paths')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    tags = models.ManyToManyField('core.Tag', related_name='learning_paths', blank=True)
    
    class Meta:
        verbose_name = _('learning path')
        verbose_name_plural = _('learning paths')
        ordering = ['title']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        """Return the URL for this learning path."""
        return f"/learning-paths/{self.slug}/"
    
    def get_completion_percentage(self, user):
        """Calculate the completion percentage for a user."""
        if not user.is_authenticated:
            return 0
        
        total_courses = self.courses.count()
        if total_courses == 0:
            return 0
        
        completed_courses = UserCourseProgress.objects.filter(
            user=user,
            course__in=self.courses.all(),
            is_completed=True
        ).count()
        
        return int((completed_courses / total_courses) * 100)


class Course(models.Model):
    """A course containing multiple modules."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    slug = models.SlugField(_('slug'), max_length=255, unique=True)
    image = models.ImageField(_('image'), upload_to='courses/', blank=True, null=True)
    learning_path = models.ForeignKey(LearningPath, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    order_in_path = models.PositiveIntegerField(_('order in path'), default=0)
    difficulty = models.CharField(_('difficulty'), max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ])
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='required_for')
    estimated_hours = models.PositiveIntegerField(_('estimated hours'), default=0)
    is_published = models.BooleanField(_('is published'), default=False)
    is_featured = models.BooleanField(_('is featured'), default=False)
    requires_subscription = models.BooleanField(_('requires subscription'), default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_courses')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    tags = models.ManyToManyField('core.Tag', related_name='courses', blank=True)
    
    class Meta:
        verbose_name = _('course')
        verbose_name_plural = _('courses')
        ordering = ['title']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        """Return the URL for this course."""
        return f"/courses/{self.slug}/"
    
    def get_completion_percentage(self, user):
        """Calculate the completion percentage for a user."""
        if not user.is_authenticated:
            return 0
        
        total_modules = self.modules.count()
        if total_modules == 0:
            return 0
        
        completed_modules = UserModuleProgress.objects.filter(
            user=user,
            module__in=self.modules.all(),
            is_completed=True
        ).count()
        
        return int((completed_modules / total_modules) * 100)


class Module(models.Model):
    """A module containing content and quizzes."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    order = models.PositiveIntegerField(_('order'), default=0)
    content = models.TextField(_('content'))
    estimated_minutes = models.PositiveIntegerField(_('estimated minutes'), default=0)
    is_published = models.BooleanField(_('is published'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('module')
        verbose_name_plural = _('modules')
        ordering = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def get_absolute_url(self):
        """Return the URL for this module."""
        return f"/courses/{self.course.slug}/modules/{self.order}/"
    
    def get_next_module(self):
        """Get the next module in the course."""
        return Module.objects.filter(
            course=self.course,
            order__gt=self.order
        ).order_by('order').first()
    
    def get_previous_module(self):
        """Get the previous module in the course."""
        return Module.objects.filter(
            course=self.course,
            order__lt=self.order
        ).order_by('-order').first()


class Quiz(models.Model):
    """A quiz containing multiple questions."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='quizzes')
    order = models.PositiveIntegerField(_('order'), default=0)
    passing_score = models.PositiveIntegerField(_('passing score'), default=70)
    time_limit_minutes = models.PositiveIntegerField(_('time limit (minutes)'), null=True, blank=True)
    is_published = models.BooleanField(_('is published'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('quiz')
        verbose_name_plural = _('quizzes')
        ordering = ['module', 'order']
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"
    
    def get_absolute_url(self):
        """Return the URL for this quiz."""
        return f"/courses/{self.module.course.slug}/modules/{self.module.order}/quizzes/{self.order}/"
    
    def calculate_score(self, user_answers):
        """Calculate the score for a set of user answers."""
        total_questions = self.questions.count()
        if total_questions == 0:
            return 0
        
        correct_answers = 0
        for question_id, answer_id in user_answers.items():
            try:
                question = self.questions.get(id=question_id)
                if question.correct_answer_id == answer_id:
                    correct_answers += 1
            except Question.DoesNotExist:
                pass
        
        return int((correct_answers / total_questions) * 100)


class Question(models.Model):
    """A question for a quiz."""
    
    QUESTION_TYPES = (
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('code', 'Code'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField(_('question text'))
    question_type = models.CharField(_('question type'), max_length=20, choices=QUESTION_TYPES)
    code_snippet = models.TextField(_('code snippet'), blank=True)
    explanation = models.TextField(_('explanation'), blank=True)
    order = models.PositiveIntegerField(_('order'), default=0)
    points = models.PositiveIntegerField(_('points'), default=1)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('question')
        verbose_name_plural = _('questions')
        ordering = ['quiz', 'order']
    
    def __str__(self):
        return f"{self.quiz.title} - Question {self.order}"
    
    @property
    def correct_answer(self):
        """Return the correct answer for this question."""
        if self.question_type == 'multiple_choice' or self.question_type == 'true_false':
            return self.answers.filter(is_correct=True).first()
        return None


class Answer(models.Model):
    """An answer option for a question."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField(_('answer text'))
    is_correct = models.BooleanField(_('is correct'), default=False)
    order = models.PositiveIntegerField(_('order'), default=0)
    
    class Meta:
        verbose_name = _('answer')
        verbose_name_plural = _('answers')
        ordering = ['question', 'order']
    
    def __str__(self):
        return f"{self.question} - Answer {self.order}"


class UserCourseProgress(models.Model):
    """Track a user's progress through a course."""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='user_progress')
    started_at = models.DateTimeField(_('started at'), auto_now_add=True)
    last_activity = models.DateTimeField(_('last activity'), auto_now=True)
    is_completed = models.BooleanField(_('is completed'), default=False)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('user course progress')
        verbose_name_plural = _('user course progress')
        unique_together = ('user', 'course')
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
    
    def mark_completed(self):
        """Mark the course as completed."""
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
            self.save()


class UserModuleProgress(models.Model):
    """Track a user's progress through a module."""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='module_progress')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='user_progress')
    started_at = models.DateTimeField(_('started at'), auto_now_add=True)
    last_activity = models.DateTimeField(_('last activity'), auto_now=True)
    is_completed = models.BooleanField(_('is completed'), default=False)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('user module progress')
        verbose_name_plural = _('user module progress')
        unique_together = ('user', 'module')
    
    def __str__(self):
        return f"{self.user.username} - {self.module.title}"
    
    def mark_completed(self):
        """Mark the module as completed."""
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
            self.save()
            
            # Check if all modules in the course are completed
            course = self.module.course
            total_modules = course.modules.count()
            completed_modules = UserModuleProgress.objects.filter(
                user=self.user,
                module__course=course,
                is_completed=True
            ).count()
            
            if total_modules > 0 and total_modules == completed_modules:
                course_progress, created = UserCourseProgress.objects.get_or_create(
                    user=self.user,
                    course=course
                )
                course_progress.mark_completed()


class UserQuizAttempt(models.Model):
    """Track a user's attempt at a quiz."""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='user_attempts')
    score = models.PositiveIntegerField(_('score'))
    passed = models.BooleanField(_('passed'))
    started_at = models.DateTimeField(_('started at'), auto_now_add=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    time_spent_seconds = models.PositiveIntegerField(_('time spent (seconds)'), default=0)
    
    class Meta:
        verbose_name = _('user quiz attempt')
        verbose_name_plural = _('user quiz attempts')
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.score}%"