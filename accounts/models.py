import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


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
    name = models.CharField(_('name'), max_length=150, null=True, blank=True)
    bio = models.TextField(_('biography'), blank=True)
    photo = models.ImageField(_('profile photo'), upload_to='profile_photos/', blank=True, null=True)
    points = models.PositiveIntegerField(_('points'), default=0)
    role = models.CharField(_('role'), max_length=20, choices=ROLE_CHOICES, default='student')
    is_verified = models.BooleanField(_('email verified'), default=False)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_active = models.DateTimeField(_('last active'), null=True, blank=True)
    
    # Social links
    github_url = models.URLField(_('GitHub URL'), blank=True)
    gitlab_url = models.URLField(_('GitLab URL'), blank=True)
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
        

    def update_points(self, amount):
        if amount == 0:
            return  # Rien à faire si l'ajout est nul

        with transaction.atomic():
            # Assure que les points ne deviennent pas négatifs
            if amount < 0 and self.points + amount < 0:
                raise ValidationError("Insufficient points to deduct.")
                
            self.points = models.F('points') + amount
            self.save(update_fields=['points'])
            self.refresh_from_db() 


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
    
class RegistrationRequest(models.Model):
    email = models.EmailField(unique=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email}: {self.code}"

    class Meta:
        verbose_name = "Registration Request"
        verbose_name_plural = "Registration Requests"

    
    def is_expired(self):
        expiration_time = self.created_at + timezone.timedelta(minutes=15)
        return timezone.now() > expiration_time
    
   
class UserProjects(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_projects')
    project_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    language = models.CharField(max_length=100,blank=True, null=True)
    stars = models.IntegerField(default=0,blank=True, null=True)
    forks = models.IntegerField(default=0,blank=True, null=True)
    image = models.ImageField(upload_to='project_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.project_name} - {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']