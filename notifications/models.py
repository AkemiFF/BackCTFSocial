import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    """User notifications."""
    
    NOTIFICATION_TYPES = (
        ('achievement', 'Achievement'),
        ('challenge', 'Challenge'),
        ('course', 'Course'),
        ('event', 'Event'),
        ('team', 'Team'),
        ('social', 'Social'),
        ('system', 'System'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(_('title'), max_length=255)
    message = models.TextField(_('message'))
    notification_type = models.CharField(_('notification type'), max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(_('priority'), max_length=10, choices=PRIORITY_LEVELS, default='medium')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), default=timezone.now)
    is_read = models.BooleanField(_('is read'), default=False)
    read_at = models.DateTimeField(_('read at'), null=True, blank=True)
    url = models.URLField(_('URL'), blank=True)
    
    # Optional foreign keys to related objects
    related_achievement = models.ForeignKey('gamification.Achievement', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_challenge = models.ForeignKey('challenges.Challenge', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_course = models.ForeignKey('learning.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_event = models.ForeignKey('events.Event', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_team = models.ForeignKey('teams.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_post = models.ForeignKey('social.Post', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    
    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"
    
    def mark_as_read(self):
        """Mark the notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
            return True
        return False
    
    def mark_as_unread(self):
        """Mark the notification as unread."""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at'])
            return True
        return False
    
    @classmethod
    def create_notification(cls, user, title, message, notification_type, **kwargs):
        """Create a new notification."""
        notification = cls(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            **kwargs
        )
        notification.save()
        return notification
    
    @classmethod
    def create_achievement_notification(cls, achievement):
        """Create a notification for a new achievement."""
        return cls.create_notification(
            user=achievement.user,
            title=f"New Achievement: {achievement.badge.name}",
            message=f"Congratulations! You've earned the {achievement.badge.name} badge.",
            notification_type='achievement',
            priority='medium',
            related_achievement=achievement,
            url=f"/achievements/{achievement.id}/"
        )
    
    @classmethod
    def create_challenge_completion_notification(cls, completion):
        """Create a notification for a completed challenge."""
        return cls.create_notification(
            user=completion.user,
            title=f"Challenge Completed: {completion.challenge.title}",
            message=f"You've successfully completed the {completion.challenge.title} challenge and earned {completion.points_earned} points!",
            notification_type='challenge',
            priority='medium',
            related_challenge=completion.challenge,
            url=f"/challenges/{completion.challenge.id}/"
        )


class NotificationPreference(models.Model):
    """User preferences for notifications."""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')
    email_notifications = models.BooleanField(_('email notifications'), default=True)
    push_notifications = models.BooleanField(_('push notifications'), default=True)
    achievement_notifications = models.BooleanField(_('achievement notifications'), default=True)
    challenge_notifications = models.BooleanField(_('challenge notifications'), default=True)
    course_notifications = models.BooleanField(_('course notifications'), default=True)
    event_notifications = models.BooleanField(_('event notifications'), default=True)
    team_notifications = models.BooleanField(_('team notifications'), default=True)
    social_notifications = models.BooleanField(_('social notifications'), default=True)
    system_notifications = models.BooleanField(_('system notifications'), default=True)
    
    class Meta:
        verbose_name = _('notification preference')
        verbose_name_plural = _('notification preferences')
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"
    
    def should_notify(self, notification_type):
        """Check if the user should be notified for a given notification type."""
        if notification_type == 'achievement':
            return self.achievement_notifications
        elif notification_type == 'challenge':
            return self.challenge_notifications
        elif notification_type == 'course':
            return self.course_notifications
        elif notification_type == 'event':
            return self.event_notifications
        elif notification_type == 'team':
            return self.team_notifications
        elif notification_type == 'social':
            return self.social_notifications
        elif notification_type == 'system':
            return self.system_notifications
        return True