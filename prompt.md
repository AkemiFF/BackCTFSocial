## accounts/models.py

```python
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import uuid


class UserManager(BaseUserManager):
    """Custom user manager for the User model."""
    
    def create_user(self, email, username, password=None, **extra_fields):
        """Create and save a regular user with the given email, username, and password."""
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not username:
            raise ValueError(_('The Username field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
        """Create and save a superuser with the given email, username, and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'administrator')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    """Custom user model for Hackitech platform."""
    
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('mentor', 'Mentor'),
        ('administrator', 'Administrator'),
        ('moderator', 'Moderator'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(_('username'), max_length=150, unique=True)
    bio = models.TextField(_('biography'), blank=True)
    photo = models.ImageField(_('profile photo'), upload_to='profile_photos/', blank=True, null=True)
    points = models.PositiveIntegerField(_('points'), default=0)
    role = models.CharField(_('role'), max_length=20, choices=ROLE_CHOICES, default='student')
    is_verified = models.BooleanField(_('email verified'), default=False)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_active = models.DateTimeField(_('last active'), null=True, blank=True)
    
    # Social links
    github_url = models.URLField(_('GitHub URL'), blank=True)
    linkedin_url = models.URLField(_('LinkedIn URL'), blank=True)
    twitter_url = models.URLField(_('Twitter URL'), blank=True)
    website_url = models.URLField(_('Website URL'), blank=True)
    
    # Security settings
    two_factor_enabled = models.BooleanField(_('two-factor authentication'), default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.username
    
    def get_full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def get_rank(self):
        """Calculate and return the user's rank based on points."""
        ranks = settings.HACKITECH['RANKS']
        for rank, threshold in sorted(ranks.items(), key=lambda x: x[1], reverse=True):
            if self.points >= threshold:
                return rank
        return 'C'  # Default rank
    
    def update_last_active(self):
        """Update the last active timestamp."""
        self.last_active = timezone.now()
        self.save(update_fields=['last_active'])


class UserProfile(models.Model):
    """Extended profile information for users."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(_('display name'), max_length=100, blank=True)
    location = models.CharField(_('location'), max_length=100, blank=True)
    skills = models.ManyToManyField('core.Skill', related_name='users', blank=True)
    interests = models.ManyToManyField('core.Tag', related_name='interested_users', blank=True)
    experience_level = models.CharField(_('experience level'), max_length=20, blank=True)
    job_title = models.CharField(_('job title'), max_length=100, blank=True)
    company = models.CharField(_('company'), max_length=100, blank=True)
    show_email = models.BooleanField(_('show email'), default=False)
    show_points = models.BooleanField(_('show points'), default=True)
    
    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
    
    def __str__(self):
        return f"Profile for {self.user.username}"


class UserSession(models.Model):
    """User session information for security tracking."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(_('session key'), max_length=40)
    ip_address = models.GenericIPAddressField(_('IP address'))
    user_agent = models.TextField(_('user agent'))
    device_type = models.CharField(_('device type'), max_length=20)
    location = models.CharField(_('location'), max_length=100, blank=True)
    started_at = models.DateTimeField(_('started at'), auto_now_add=True)
    last_activity = models.DateTimeField(_('last activity'), auto_now=True)
    is_active = models.BooleanField(_('is active'), default=True)
    
    class Meta:
        verbose_name = _('user session')
        verbose_name_plural = _('user sessions')
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"Session for {self.user.username} from {self.ip_address}"


class UserFollowing(models.Model):
    """Model to track user following relationships."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('user following')
        verbose_name_plural = _('user followings')
        unique_together = ('user', 'following_user')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} follows {self.following_user.username}"
```

## learning/models.py

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import uuid


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
```

## challenges/models.py

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import uuid


class Challenge(models.Model):
    """A hacking challenge for users to solve."""
    
    DIFFICULTY_CHOICES = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('expert', 'Expert'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    difficulty = models.CharField(_('difficulty'), max_length=20, choices=DIFFICULTY_CHOICES)
    points = models.PositiveIntegerField(_('points'))
    flag = models.CharField(_('flag'), max_length=255)
    category = models.ForeignKey('core.Category', on_delete=models.SET_NULL, null=True, related_name='challenges')
    tags = models.ManyToManyField('core.Tag', related_name='challenges', blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_challenges')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(_('is featured'), default=False)
    requires_subscription = models.BooleanField(_('requires subscription'), default=False)
    max_attempts = models.PositiveIntegerField(_('maximum attempts'), null=True, blank=True)
    time_limit_minutes = models.PositiveIntegerField(_('time limit (minutes)'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('challenge')
        verbose_name_plural = _('challenges')
        ordering = ['difficulty', 'title']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        """Return the URL for this challenge."""
        return f"/challenges/{self.id}/"
    
    def verify_flag(self, submitted_flag):
        """Verify if the submitted flag is correct."""
        return submitted_flag.strip() == self.flag.strip()
    
    def get_points_for_user(self, user, hint_count=0):
        """Calculate points for a user based on hints used."""
        if hint_count == 0:
            return self.points
        
        # Reduce points based on hints used
        max_penalty = settings.HACKITECH.get('MAX_HINT_PENALTY', 0.5)
        hints_count = self.hints.count()
        
        if hints_count == 0:
            return self.points
        
        penalty_per_hint = max_penalty / hints_count
        penalty = min(penalty_per_hint * hint_count, max_penalty)
        
        return int(self.points * (1 - penalty))


class Hint(models.Model):
    """A hint for a challenge."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='hints')
    content = models.TextField(_('content'))
    order = models.PositiveIntegerField(_('order'), default=0)
    cost = models.PositiveIntegerField(_('cost'), default=0, help_text=_('Cost in points to unlock this hint'))
    
    class Meta:
        verbose_name = _('hint')
        verbose_name_plural = _('hints')
        ordering = ['challenge', 'order']
    
    def __str__(self):
        return f"{self.challenge.title} - Hint {self.order}"


class Resource(models.Model):
    """A resource for a challenge."""
    
    RESOURCE_TYPES = (
        ('file', 'File'),
        ('link', 'Link'),
        ('docker', 'Docker Container'),
        ('vm', 'Virtual Machine'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='resources')
    name = models.CharField(_('name'), max_length=100)
    resource_type = models.CharField(_('resource type'), max_length=20, choices=RESOURCE_TYPES)
    file = models.FileField(_('file'), upload_to='challenge_resources/', blank=True, null=True)
    url = models.URLField(_('URL'), blank=True)
    docker_image = models.CharField(_('docker image'), max_length=255, blank=True)
    description = models.TextField(_('description'), blank=True)
    
    class Meta:
        verbose_name = _('resource')
        verbose_name_plural = _('resources')
    
    def __str__(self):
        return f"{self.challenge.title} - {self.name}"


class Submission(models.Model):
    """A user's submission for a challenge."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='submissions')
    submitted_flag = models.CharField(_('submitted flag'), max_length=255)
    is_correct = models.BooleanField(_('is correct'))
    submission_time = models.DateTimeField(_('submission time'), auto_now_add=True)
    hints_used = models.ManyToManyField(Hint, related_name='used_in_submissions', blank=True)
    points_awarded = models.PositiveIntegerField(_('points awarded'), default=0)
    attempt_number = models.PositiveIntegerField(_('attempt number'), default=1)
    time_spent_seconds = models.PositiveIntegerField(_('time spent (seconds)'), default=0)
    
    class Meta:
        verbose_name = _('submission')
        verbose_name_plural = _('submissions')
        ordering = ['-submission_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.title} - {'Correct' if self.is_correct else 'Incorrect'}"
    
    def save(self, *args, **kwargs):
        """Override save to verify flag and award points if not already set."""
        if not self.id:  # New submission
            self.is_correct = self.challenge.verify_flag(self.submitted_flag)
            
            # Count previous attempts
            previous_attempts = Submission.objects.filter(
                user=self.user,
                challenge=self.challenge
            ).count()
            self.attempt_number = previous_attempts + 1
            
            # Award points if correct and first correct submission
            if self.is_correct and not Submission.objects.filter(
                user=self.user,
                challenge=self.challenge,
                is_correct=True
            ).exists():
                hint_count = self.hints_used.count()
                self.points_awarded = self.challenge.get_points_for_user(self.user, hint_count)
                
                # Update user points
                self.user.points += self.points_awarded
                self.user.save(update_fields=['points'])
        
        super().save(*args, **kwargs)


class UserHint(models.Model):
    """Track which hints a user has unlocked for a challenge."""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='unlocked_hints')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='user_hints')
    hint = models.ForeignKey(Hint, on_delete=models.CASCADE, related_name='unlocked_by_users')
    unlocked_at = models.DateTimeField(_('unlocked at'), auto_now_add=True)
    points_deducted = models.PositiveIntegerField(_('points deducted'), default=0)
    
    class Meta:
        verbose_name = _('user hint')
        verbose_name_plural = _('user hints')
        unique_together = ('user', 'hint')
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.title} - Hint {self.hint.order}"


class ChallengeRating(models.Model):
    """User ratings for challenges."""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='challenge_ratings')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='ratings')
    rating = models.PositiveSmallIntegerField(_('rating'), choices=[(i, i) for i in range(1, 6)])
    feedback = models.TextField(_('feedback'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('challenge rating')
        verbose_name_plural = _('challenge ratings')
        unique_together = ('user', 'challenge')
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.title} - {self.rating}/5"


class ChallengeCompletion(models.Model):
    """Track when a user completes a challenge."""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='completed_challenges')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='completions')
    completed_at = models.DateTimeField(_('completed at'), auto_now_add=True)
    points_earned = models.PositiveIntegerField(_('points earned'))
    time_spent_seconds = models.PositiveIntegerField(_('time spent (seconds)'), default=0)
    attempts = models.PositiveIntegerField(_('attempts'), default=1)
    
    class Meta:
        verbose_name = _('challenge completion')
        verbose_name_plural = _('challenge completions')
        unique_together = ('user', 'challenge')
    
    def __str__(self):
        return f"{self.user.username} completed {self.challenge.title}"
```

## social/models.py

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import uuid


class Post(models.Model):
    """User posts for the social feed."""
    
    POST_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('link', 'Link'),
        ('code', 'Code'),
        ('project', 'Project'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(_('content'))
    post_type = models.CharField(_('post type'), max_length=20, choices=POST_TYPES, default='text')
    image = models.ImageField(_('image'), upload_to='post_images/', blank=True, null=True)
    code_snippet = models.TextField(_('code snippet'), blank=True)
    code_language = models.CharField(_('code language'), max_length=50, blank=True)
    link_url = models.URLField(_('link URL'), blank=True)
    link_title = models.CharField(_('link title'), max_length=255, blank=True)
    link_description = models.TextField(_('link description'), blank=True)
    link_image = models.URLField(_('link image'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_edited = models.BooleanField(_('is edited'), default=False)
    is_pinned = models.BooleanField(_('is pinned'), default=False)
    is_public = models.BooleanField(_('is public'), default=True)
    tags = models.ManyToManyField('core.Tag', related_name='posts', blank=True)
    mentions = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='mentioned_in_posts', blank=True)
    
    class Meta:
        verbose_name = _('post')
        verbose_name_plural = _('posts')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s post - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_absolute_url(self):
        """Return the URL for this post."""
        return f"/posts/{self.id}/"
    
    def add_post(self):
        """Add a new post."""
        self.save()
    
    def edit_post(self, content):
        """Edit an existing post."""
        self.content = content
        self.is_edited = True
        self.updated_at = timezone.now()
        self.save()
    
    def delete_post(self):
        """Delete a post."""
        self.delete()
    
    @property
    def like_count(self):
        """Get the number of likes for this post."""
        return self.interactions.filter(interaction_type='like').count()
    
    @property
    def comment_count(self):
        """Get the number of comments for this post."""
        return self.comments.count()
    
    @property
    def share_count(self):
        """Get the number of shares for this post."""
        return self.interactions.filter(interaction_type='share').count()


class Comment(models.Model):
    """Comments on posts."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(_('content'))
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_edited = models.BooleanField(_('is edited'), default=False)
    mentions = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='mentioned_in_comments', blank=True)
    
    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.post}"
    
    def add_comment(self):
        """Add a new comment."""
        self.save()
    
    def edit_comment(self, content):
        """Edit an existing comment."""
        self.content = content
        self.is_edited = True
        self.updated_at = timezone.now()
        self.save()
    
    def delete_comment(self):
        """Delete a comment."""
        self.delete()
    
    @property
    def like_count(self):
        """Get the number of likes for this comment."""
        return self.interactions.filter(interaction_type='like').count()
    
    @property
    def is_reply(self):
        """Check if this comment is a reply to another comment."""
        return self.parent is not None


class SocialInteraction(models.Model):
    """Social interactions like likes, shares, etc."""
    
    INTERACTION_TYPES = (
        ('like', 'Like'),
        ('share', 'Share'),
        ('save', 'Save'),
        ('report', 'Report'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='social_interactions')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='interactions', null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='interactions', null=True, blank=True)
    interaction_type = models.CharField(_('interaction type'), max_length=20, choices=INTERACTION_TYPES)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('social interaction')
        verbose_name_plural = _('social interactions')
        unique_together = [
            ('user', 'post', 'interaction_type'),
            ('user', 'comment', 'interaction_type'),
        ]
    
    def __str__(self):
        target = self.post or self.comment
        return f"{self.user.username} {self.interaction_type}d {target}"
    
    def like_content(self):
        """Like a post or comment."""
        self.interaction_type = 'like'
        self.save()
    
    def share_content(self):
        """Share a post."""
        if not self.post:
            raise ValueError("Can only share posts, not comments")
        self.interaction_type = 'share'
        self.save()
    
    def save_content(self):
        """Save a post for later."""
        self.interaction_type = 'save'
        self.save()
    
    def report_content(self):
        """Report a post or comment."""
        self.interaction_type = 'report'
        self.save()


class Conversation(models.Model):
    """Private conversations between users."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_group = models.BooleanField(_('is group'), default=False)
    name = models.CharField(_('name'), max_length=255, blank=True)
    
    class Meta:
        verbose_name = _('conversation')
        verbose_name_plural = _('conversations')
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.is_group and self.name:
            return f"Group: {self.name}"
        participants = self.participants.all()
        if participants.count() <= 3:
            return ", ".join([user.username for user in participants])
        return f"{participants.first().username} and {participants.count() - 1} others"
    
    def get_absolute_url(self):
        """Return the URL for this conversation."""
        return f"/messages/{self.id}/"
    
    @property
    def last_message(self):
        """Get the last message in this conversation."""
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    """Messages within a conversation."""
    
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('code', 'Code'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(_('message type'), max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField(_('content'))
    image = models.ImageField(_('image'), upload_to='message_images/', blank=True, null=True)
    file = models.FileField(_('file'), upload_to='message_files/', blank=True, null=True)
    code_snippet = models.TextField(_('code snippet'), blank=True)
    code_language = models.CharField(_('code language'), max_length=50, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    is_read = models.BooleanField(_('is read'), default=False)
    read_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='read_messages', blank=True)
    
    class Meta:
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} in {self.conversation}"
    
    def mark_as_read(self, user):
        """Mark the message as read by a user."""
        if user != self.sender and user in self.conversation.participants.all():
            self.read_by.add(user)
            if self.read_by.count() == self.conversation.participants.count() - 1:
                self.is_read = True
                self.save()


class Project(models.Model):
    """User projects to showcase."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'))
    image = models.ImageField(_('image'), upload_to='project_images/', blank=True, null=True)
    repository_url = models.URLField(_('repository URL'), blank=True)
    demo_url = models.URLField(_('demo URL'), blank=True)
    technologies = models.ManyToManyField('core.Skill', related_name='projects', blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_public = models.BooleanField(_('is public'), default=True)
    
    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s project: {self.title}"
    
    def get_absolute_url(self):
        """Return the URL for this project."""
        return f"/projects/{self.id}/"
```
