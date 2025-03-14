# gamification/models.py
import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = settings.AUTH_USER_MODEL


class Point(models.Model):
    """
    Points earned by users for various activities.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='point_records',
        verbose_name=_("User")
    )
    amount = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Amount")
    )
    source = models.CharField(
        max_length=100,
        verbose_name=_("Source")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at")
    )
    
    class Meta:
        verbose_name = _("Point")
        verbose_name_plural = _("Points")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['source']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.amount} points from {self.source}"


class Level(models.Model):
    """
    Levels that users can achieve based on points.
    """
    number = models.PositiveIntegerField(
        unique=True,
        verbose_name=_("Level number")
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Name")
    )
    points_required = models.PositiveIntegerField(
        verbose_name=_("Points required")
    )
    icon = models.ImageField(
        upload_to='gamification/levels/',
        blank=True,
        null=True,
        verbose_name=_("Icon")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    
    class Meta:
        verbose_name = _("Level")
        verbose_name_plural = _("Levels")
        ordering = ['number']
    
    def __str__(self):
        return f"Level {self.number}: {self.name}"


class UserLevel(models.Model):
    """
    Tracks the current level of each user.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='level',
        verbose_name=_("User")
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name=_("Level")
    )
    total_points = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total points")
    )
    points_to_next_level = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Points to next level")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated at")
    )
    
    class Meta:
        verbose_name = _("User Level")
        verbose_name_plural = _("User Levels")
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['level']),
            models.Index(fields=['total_points']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - Level {self.level.number}"
    
    def calculate_points_to_next_level(self):
        """Calculate points needed to reach the next level."""
        try:
            next_level = Level.objects.filter(
                number__gt=self.level.number
            ).order_by('number').first()
            
            if next_level:
                return next_level.points_required - self.total_points
            return 0
        except Level.DoesNotExist:
            return 0
    
    def update_level(self):
        """Update user level based on total points."""
        current_level = self.level
        
        # Find the highest level the user qualifies for
        new_level = Level.objects.filter(
            points_required__lte=self.total_points
        ).order_by('-number').first()
        
        if new_level and new_level != current_level:
            self.level = new_level
            self.save()
            
            # Create level up event
            LevelUpEvent.objects.create(
                user=self.user,
                from_level=current_level,
                to_level=new_level
            )
            
            return True
        return False
    
    def save(self, *args, **kwargs):
        # Calculate points to next level
        self.points_to_next_level = self.calculate_points_to_next_level()
        super().save(*args, **kwargs)


class LevelUpEvent(models.Model):
    """
    Records when a user levels up.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='level_ups',
        verbose_name=_("User")
    )
    from_level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='level_ups_from',
        verbose_name=_("From level")
    )
    to_level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='level_ups_to',
        verbose_name=_("To level")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at")
    )
    
    class Meta:
        verbose_name = _("Level Up Event")
        verbose_name_plural = _("Level Up Events")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} leveled up from {self.from_level.number} to {self.to_level.number}"


class Badge(models.Model):
    """
    Badges that users can earn.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Name")
    )
    description = models.TextField(
        verbose_name=_("Description")
    )
    icon = models.ImageField(
        upload_to='gamification/badges/',
        verbose_name=_("Icon")
    )
    category = models.CharField(
        max_length=50,
        verbose_name=_("Category")
    )
    points_value = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Points value")
    )
    is_hidden = models.BooleanField(
        default=False,
        verbose_name=_("Is hidden")
    )
    
    class Meta:
        verbose_name = _("Badge")
        verbose_name_plural = _("Badges")
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserBadge(models.Model):
    """
    Badges earned by users.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='badges',
        verbose_name=_("User")
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name=_("Badge")
    )
    earned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Earned at")
    )
    
    class Meta:
        verbose_name = _("User Badge")
        verbose_name_plural = _("User Badges")
        unique_together = ['user', 'badge']
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['user', 'earned_at']),
            models.Index(fields=['badge']),
        ]
    
    def __str__(self):
        return f"{self.user.username} earned {self.badge.name}"
    
    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        # Award points for earning a badge
        if is_new and self.badge.points_value > 0:
            Point.objects.create(
                user=self.user,
                amount=self.badge.points_value,
                source='badge',
                description=f"Earned badge: {self.badge.name}"
            )


class Challenge(models.Model):
    """
    Challenges that users can complete.
    """
    DIFFICULTY_CHOICES = [
        ('easy', _('Easy')),
        ('medium', _('Medium')),
        ('hard', _('Hard')),
        ('expert', _('Expert')),
    ]
    
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('inactive', _('Inactive')),
        ('scheduled', _('Scheduled')),
        ('completed', _('Completed')),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name=_("Title")
    )
    description = models.TextField(
        verbose_name=_("Description")
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium',
        verbose_name=_("Difficulty")
    )
    points_reward = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Points reward")
    )
    badge_reward = models.ForeignKey(
        Badge,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='challenges',
        verbose_name=_("Badge reward")
    )
    start_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Start date")
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("End date")
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name=_("Status")
    )
    completion_criteria = models.JSONField(
        default=dict,
        verbose_name=_("Completion criteria")
    )
    max_completions = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Maximum completions")
    )
    
    class Meta:
        verbose_name = _("Challenge")
        verbose_name_plural = _("Challenges")
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['difficulty']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def is_active(self):
        now = timezone.now()
        if self.status != 'active':
            return False
        if self.end_date and now > self.end_date:
            return False
        return now >= self.start_date


class UserChallenge(models.Model):
    """
    Tracks user progress on challenges.
    """
    STATUS_CHOICES = [
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('abandoned', _('Abandoned')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='challenges',
        verbose_name=_("User")
    )
    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name=_("Challenge")
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='in_progress',
        verbose_name=_("Status")
    )
    progress = models.JSONField(
        default=dict,
        verbose_name=_("Progress")
    )
    progress_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Progress percentage")
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Started at")
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Completed at")
    )
    
    class Meta:
        verbose_name = _("User Challenge")
        verbose_name_plural = _("User Challenges")
        unique_together = ['user', 'challenge']
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['challenge']),
            models.Index(fields=['completed_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.title} ({self.get_status_display()})"
    
    def complete(self):
        """Mark the challenge as completed and award rewards."""
        if self.status != 'completed':
            self.status = 'completed'
            self.progress_percentage = 100
            self.completed_at = timezone.now()
            self.save()
            
            # Award points
            if self.challenge.points_reward > 0:
                Point.objects.create(
                    user=self.user,
                    amount=self.challenge.points_reward,
                    source='challenge',
                    description=f"Completed challenge: {self.challenge.title}"
                )
            
            # Award badge if applicable
            if self.challenge.badge_reward:
                UserBadge.objects.get_or_create(
                    user=self.user,
                    badge=self.challenge.badge_reward
                )
            
            return True
        return False
    
    def update_progress(self, progress_data):
        """Update the progress of the challenge."""
        self.progress.update(progress_data)
        
        # Calculate progress percentage based on completion criteria
        criteria = self.challenge.completion_criteria
        if criteria:
            completed = 0
            total = len(criteria)
            
            for key, required_value in criteria.items():
                current_value = self.progress.get(key, 0)
                if current_value >= required_value:
                    completed += 1
            
            self.progress_percentage = int((completed / total) * 100)
            
            # Auto-complete if 100%
            if self.progress_percentage >= 100:
                self.complete()
            else:
                self.save()
        
        return self.progress_percentage


class Achievement(models.Model):
    """
    Achievements that users can unlock.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Name")
    )
    description = models.TextField(
        verbose_name=_("Description")
    )
    icon = models.ImageField(
        upload_to='gamification/achievements/',
        verbose_name=_("Icon")
    )
    points_reward = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Points reward")
    )
    badge_reward = models.ForeignKey(
        Badge,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='achievements',
        verbose_name=_("Badge reward")
    )
    is_hidden = models.BooleanField(
        default=False,
        verbose_name=_("Is hidden")
    )
    criteria = models.JSONField(
        default=dict,
        verbose_name=_("Criteria")
    )
    
    class Meta:
        verbose_name = _("Achievement")
        verbose_name_plural = _("Achievements")
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """
    Achievements unlocked by users.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='achievements',
        verbose_name=_("User")
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name=_("Achievement")
    )
    unlocked_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Unlocked at")
    )
    
    class Meta:
        verbose_name = _("User Achievement")
        verbose_name_plural = _("User Achievements")
        unique_together = ['user', 'achievement']
        ordering = ['-unlocked_at']
        indexes = [
            models.Index(fields=['user', 'unlocked_at']),
            models.Index(fields=['achievement']),
        ]
    
    def __str__(self):
        return f"{self.user.username} unlocked {self.achievement.name}"
    
    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        if is_new:
            # Award points
            if self.achievement.points_reward > 0:
                Point.objects.create(
                    user=self.user,
                    amount=self.achievement.points_reward,
                    source='achievement',
                    description=f"Unlocked achievement: {self.achievement.name}"
                )
            
            # Award badge if applicable
            if self.achievement.badge_reward:
                UserBadge.objects.get_or_create(
                    user=self.user,
                    badge=self.achievement.badge_reward
                )


class Reward(models.Model):
    """
    Rewards that users can redeem with points.
    """
    name = models.CharField(
        max_length=100,
        verbose_name=_("Name")
    )
    description = models.TextField(
        verbose_name=_("Description")
    )
    image = models.ImageField(
        upload_to='gamification/rewards/',
        blank=True,
        null=True,
        verbose_name=_("Image")
    )
    points_cost = models.PositiveIntegerField(
        verbose_name=_("Points cost")
    )
    quantity_available = models.IntegerField(
        default=-1,  # -1 means unlimited
        verbose_name=_("Quantity available")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is active")
    )
    start_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Start date")
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("End date")
    )
    redemption_instructions = models.TextField(
        blank=True,
        verbose_name=_("Redemption instructions")
    )
    
    class Meta:
        verbose_name = _("Reward")
        verbose_name_plural = _("Rewards")
        ordering = ['points_cost', 'name']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['points_cost']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.points_cost} points)"
    
    @property
    def is_available(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.quantity_available == 0:
            return False
        if self.end_date and now > self.end_date:
            return False
        return now >= self.start_date


class UserReward(models.Model):
    """
    Rewards redeemed by users.
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('fulfilled', _('Fulfilled')),
        ('cancelled', _('Cancelled')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='rewards',
        verbose_name=_("User")
    )
    reward = models.ForeignKey(
        Reward,
        on_delete=models.CASCADE,
        related_name='redemptions',
        verbose_name=_("Reward")
    )
    points_spent = models.PositiveIntegerField(
        verbose_name=_("Points spent")
    )
    redeemed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Redeemed at")
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_("Status")
    )
    fulfillment_details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Fulfillment details")
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        default=uuid.uuid4,
        verbose_name=_("Redemption code")
    )
    
    class Meta:
        verbose_name = _("User Reward")
        verbose_name_plural = _("User Rewards")
        ordering = ['-redeemed_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['reward']),
            models.Index(fields=['redeemed_at']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"{self.user.username} redeemed {self.reward.name}"


class Leaderboard(models.Model):
    """
    Leaderboards for different categories and time periods.
    """
    PERIOD_CHOICES = [
        ('daily', _('Daily')),
        ('weekly', _('Weekly')),
        ('monthly', _('Monthly')),
        ('yearly', _('Yearly')),
        ('all_time', _('All Time')),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name=_("Name")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    category = models.CharField(
        max_length=50,
        verbose_name=_("Category")
    )
    period = models.CharField(
        max_length=10,
        choices=PERIOD_CHOICES,
        default='weekly',
        verbose_name=_("Period")
    )
    start_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Start date")
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("End date")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is active")
    )
    
    class Meta:
        verbose_name = _("Leaderboard")
        verbose_name_plural = _("Leaderboards")
        unique_together = ['category', 'period', 'start_date']
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['category', 'period']),
            models.Index(fields=['is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_period_display()})"


class LeaderboardEntry(models.Model):
    """
    Entries in a leaderboard.
    """
    leaderboard = models.ForeignKey(
        Leaderboard,
        on_delete=models.CASCADE,
        related_name='entries',
        verbose_name=_("Leaderboard")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='leaderboard_entries',
        verbose_name=_("User")
    )
    score = models.IntegerField(
        default=0,
        verbose_name=_("Score")
    )
    rank = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Rank")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated at")
    )
    
    class Meta:
        verbose_name = _("Leaderboard Entry")
        verbose_name_plural = _("Leaderboard Entries")
        unique_together = ['leaderboard', 'user']
        ordering = ['-score']
        indexes = [
            models.Index(fields=['leaderboard', 'score']),
            models.Index(fields=['user']),
            models.Index(fields=['rank']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.score} points on {self.leaderboard.name}"