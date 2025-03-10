import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


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