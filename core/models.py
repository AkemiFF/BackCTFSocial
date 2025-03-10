import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class BaseEntity(models.Model):
    """Base abstract model for common fields."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        abstract = True


class Tag(models.Model):
    """Tags for categorizing content."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=50, unique=True)
    slug = models.SlugField(_('slug'), max_length=50, unique=True)
    description = models.TextField(_('description'), blank=True)
    color = models.CharField(_('color'), max_length=20, blank=True)
    
    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Category(models.Model):
    """Categories for organizing content."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    icon = models.CharField(_('icon'), max_length=50, blank=True)
    color = models.CharField(_('color'), max_length=20, blank=True)
    
    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def full_name(self):
        """Get the full category name including parent categories."""
        if self.parent:
            return f"{self.parent.full_name} > {self.name}"
        return self.name


class Skill(models.Model):
    """Skills that users can have or learn."""
    
    SKILL_TYPES = (
        ('technical', 'Technical'),
        ('soft', 'Soft'),
        ('language', 'Language'),
        ('tool', 'Tool'),
        ('framework', 'Framework'),
        ('methodology', 'Methodology'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    skill_type = models.CharField(_('skill type'), max_length=20, choices=SKILL_TYPES)
    icon = models.CharField(_('icon'), max_length=50, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    related_skills = models.ManyToManyField('self', symmetrical=True, blank=True)
    
    class Meta:
        verbose_name = _('skill')
        verbose_name_plural = _('skills')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Setting(models.Model):
    """System settings stored as key-value pairs."""
    
    key = models.CharField(_('key'), max_length=100, unique=True)
    value = models.TextField(_('value'))
    description = models.TextField(_('description'), blank=True)
    is_public = models.BooleanField(_('is public'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('setting')
        verbose_name_plural = _('settings')
        ordering = ['key']
    
    def __str__(self):
        return self.key


class Feedback(models.Model):
    """User feedback for the platform."""
    
    FEEDBACK_TYPES = (
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
        ('improvement', 'Improvement'),
        ('general', 'General Feedback'),
    )
    
    STATUS_CHOICES = (
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='feedback')
    feedback_type = models.CharField(_('feedback type'), max_length=20, choices=FEEDBACK_TYPES)
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'))
    screenshot = models.ImageField(_('screenshot'), upload_to='feedback_screenshots/', blank=True, null=True)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    resolved_at = models.DateTimeField(_('resolved at'), null=True, blank=True)
    admin_notes = models.TextField(_('admin notes'), blank=True)
    
    class Meta:
        verbose_name = _('feedback')
        verbose_name_plural = _('feedback')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_feedback_type_display()}: {self.title}"
    
    def resolve(self, notes=None):
        """Mark the feedback as resolved."""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save(update_fields=['status', 'resolved_at', 'admin_notes'])
        return True


class Audit(models.Model):
    """Audit log for tracking important actions."""
    
    ACTION_TYPES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('view', 'View'),
        ('download', 'Download'),
        ('other', 'Other'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(_('action'), max_length=20, choices=ACTION_TYPES)
    entity_type = models.CharField(_('entity type'), max_length=100)
    entity_id = models.CharField(_('entity ID'), max_length=100, blank=True)
    description = models.TextField(_('description'))
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    timestamp = models.DateTimeField(_('timestamp'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('audit log')
        verbose_name_plural = _('audit logs')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_action_display()} {self.entity_type} by {self.user.username if self.user else 'Unknown'}"
    
    @classmethod
    def log(cls, user, action, entity_type, entity_id=None, description=None, request=None):
        """Create a new audit log entry."""
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        return cls.objects.create(
            user=user,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else '',
            description=description or f"{action} {entity_type}",
            ip_address=ip_address,
            user_agent=user_agent
        )