import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from teams.models import Team


class Badge(models.Model):
    """Badges that users can earn."""
    
    BADGE_TYPES = (
        ('achievement', 'Achievement'),
        ('skill', 'Skill'),
        ('participation', 'Participation'),
        ('contribution', 'Contribution'),
        ('special', 'Special'),
    )
    
    BADGE_LEVELS = (
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'))
    icon = models.ImageField(_('icon'), upload_to='badge_icons/')
    badge_type = models.CharField(_('badge type'), max_length=20, choices=BADGE_TYPES)
    level = models.CharField(_('level'), max_length=20, choices=BADGE_LEVELS, default='bronze')
    points = models.PositiveIntegerField(_('points'), default=0)
    requirement = models.TextField(_('requirement'), blank=True)
    is_hidden = models.BooleanField(_('is hidden'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('badge')
        verbose_name_plural = _('badges')
        ordering = ['badge_type', 'level', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"
    
    def award_to_user(self, user):
        """Award this badge to a user."""
        if not Achievement.objects.filter(user=user, badge=self).exists():
            achievement = Achievement.objects.create(
                user=user,
                badge=self,
                points=self.points
            )
            
            # Update user points
            user.points += self.points
            user.save(update_fields=['points'])
            
            return achievement
        return None


class Achievement(models.Model):
    """Achievements earned by users."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='achievements')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='achievements')
    earned_at = models.DateTimeField(_('earned at'), auto_now_add=True)
    points = models.PositiveIntegerField(_('points'), default=0)
    
    class Meta:
        verbose_name = _('achievement')
        verbose_name_plural = _('achievements')
        unique_together = ('user', 'badge')
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} earned {self.badge.name}"


class Score(models.Model):
    """Score records for users and teams."""
    
    SCORE_TYPES = (
        ('challenge', 'Challenge'),
        ('quiz', 'Quiz'),
        ('contribution', 'Contribution'),
        ('event', 'Event'),
        ('bonus', 'Bonus'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scores', null=True, blank=True)
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='scores', null=True, blank=True)
    points = models.IntegerField(_('points'))
    score_type = models.CharField(_('score type'), max_length=20, choices=SCORE_TYPES)
    description = models.CharField(_('description'), max_length=255)
    earned_at = models.DateTimeField(_('earned at'), auto_now_add=True)
    challenge = models.ForeignKey('challenges.Challenge', on_delete=models.SET_NULL, null=True, blank=True, related_name='scores')
    quiz = models.ForeignKey('learning.Quiz', on_delete=models.SET_NULL, null=True, blank=True, related_name='scores')
    event = models.ForeignKey('events.Event', on_delete=models.SET_NULL, null=True, blank=True, related_name='scores')
    
    class Meta:
        verbose_name = _('score')
        verbose_name_plural = _('scores')
        ordering = ['-earned_at']
    
    def __str__(self):
        if self.user:
            return f"{self.user.username} earned {self.points} points for {self.description}"
        elif self.team:
            return f"{self.team.name} earned {self.points} points for {self.description}"
        return f"Score: {self.points} points for {self.description}"
    
    def save(self, *args, **kwargs):
        """Ensure either user or team is set, but not both."""
        if not self.user and not self.team:
            raise ValueError(_("Either user or team must be set"))
        if self.user and self.team:
            raise ValueError(_("Cannot set both user and team"))
        super().save(*args, **kwargs)


class ScoreHistory(models.Model):
    """Historical record of user and team scores."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='score_history', null=True, blank=True)
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='score_history', null=True, blank=True)
    points = models.IntegerField(_('points'))
    cumulative_points = models.IntegerField(_('cumulative points'))
    recorded_at = models.DateTimeField(_('recorded at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('score history')
        verbose_name_plural = _('score histories')
        ordering = ['-recorded_at']
    
    def __str__(self):
        if self.user:
            return f"{self.user.username}: {self.points} points ({self.recorded_at.strftime('%Y-%m-%d')})"
        elif self.team:
            return f"{self.team.name}: {self.points} points ({self.recorded_at.strftime('%Y-%m-%d')})"
        return f"Score history: {self.points} points ({self.recorded_at.strftime('%Y-%m-%d')})"


class Leaderboard(models.Model):
    """Leaderboards for different categories and time periods."""
    
    LEADERBOARD_TYPES = (
        ('global', 'Global'),
        ('challenge', 'Challenge'),
        ('course', 'Course'),
        ('event', 'Event'),
        ('team', 'Team'),
    )
    
    TIME_PERIODS = (
        ('all_time', 'All Time'),
        ('yearly', 'Yearly'),
        ('monthly', 'Monthly'),
        ('weekly', 'Weekly'),
        ('daily', 'Daily'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    leaderboard_type = models.CharField(_('leaderboard type'), max_length=20, choices=LEADERBOARD_TYPES)
    time_period = models.CharField(_('time period'), max_length=20, choices=TIME_PERIODS, default='all_time')
    challenge = models.ForeignKey('challenges.Challenge', on_delete=models.SET_NULL, null=True, blank=True, related_name='leaderboards')
    course = models.ForeignKey('learning.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='leaderboards')
    event = models.ForeignKey('events.Event', on_delete=models.SET_NULL, null=True, blank=True, related_name='leaderboards')
    is_active = models.BooleanField(_('is active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('leaderboard')
        verbose_name_plural = _('leaderboards')
        ordering = ['leaderboard_type', 'time_period', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_time_period_display()})"
    
    def get_top_users(self, limit=10):
        """Get the top users for this leaderboard."""
        from django.db.models import Sum

        # Define the time range based on the time period
        now = timezone.now()
        if self.time_period == 'daily':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.time_period == 'weekly':
            start_date = now - timezone.timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.time_period == 'monthly':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif self.time_period == 'yearly':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # all_time
            start_date = None
        
        # Build the query based on the leaderboard type and time period
        query = Score.objects.filter(user__isnull=False)
        
        if start_date:
            query = query.filter(earned_at__gte=start_date)
        
        if self.leaderboard_type == 'challenge' and self.challenge:
            query = query.filter(challenge=self.challenge)
        elif self.leaderboard_type == 'course' and self.course:
            query = query.filter(quiz__module__course=self.course)
        elif self.leaderboard_type == 'event' and self.event:
            query = query.filter(event=self.event)
        
        # Aggregate scores by user
        user_scores = query.values('user').annotate(
            total_points=Sum('points')
        ).order_by('-total_points')[:limit]
        
        # Get the actual user objects
        result = []
        for entry in user_scores:
            user = settings.AUTH_USER_MODEL.objects.get(id=entry['user'])
            result.append({
                'user': user,
                'points': entry['total_points']
            })
        
        return result
    
    def get_top_teams(self, limit=10):
        """Get the top teams for this leaderboard."""
        from django.db.models import Sum

        # Define the time range based on the time period
        now = timezone.now()
        if self.time_period == 'daily':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.time_period == 'weekly':
            start_date = now - timezone.timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.time_period == 'monthly':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif self.time_period == 'yearly':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # all_time
            start_date = None
        
        # Build the query based on the leaderboard type and time period
        query = Score.objects.filter(team__isnull=False)
        
        if start_date:
            query = query.filter(earned_at__gte=start_date)
        
        if self.leaderboard_type == 'challenge' and self.challenge:
            query = query.filter(challenge=self.challenge)
        elif self.leaderboard_type == 'event' and self.event:
            query = query.filter(event=self.event)
        
        # Aggregate scores by team
        team_scores = query.values('team').annotate(
            total_points=Sum('points')
        ).order_by('-total_points')[:limit]
        
        # Get the actual team objects
        result = []
        for entry in team_scores:
            team = Team.objects.get(id=entry['team'])
            result.append({
                'team': team,
                'points': entry['total_points']
            })
        
        return result