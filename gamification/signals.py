# gamification/signals.py
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import (LeaderboardEntry, Level, Point, UserAchievement,
                     UserBadge, UserChallenge, UserLevel, UserReward)

User = get_user_model()

@receiver(post_save, sender=UserLevel)
def check_level_achievements(sender, instance, **kwargs):
    """Check if user has unlocked any level-based achievements."""
    from .services import achievement_service
    achievement_service.check_level_achievements(instance.user, instance.level)


@receiver(post_save, sender=UserBadge)
def check_badge_achievements(sender, instance, created, **kwargs):
    """Check if user has unlocked any badge-based achievements."""
    if created:
        from .services import achievement_service
        achievement_service.check_badge_achievements(instance.user)


@receiver(post_save, sender=UserChallenge)
def check_challenge_achievements(sender, instance, **kwargs):
    """Check if user has unlocked any challenge-based achievements."""
    if instance.status == 'completed':
        from .services import achievement_service
        achievement_service.check_challenge_achievements(instance.user)


@receiver(post_save, sender=UserReward)
def process_reward_redemption(sender, instance, created, **kwargs):
    """Process reward redemption and deduct points."""
    if created:
        # Deduct points from user
        Point.objects.create(
            user=instance.user,
            amount=-instance.points_spent,
            source='reward_redemption',
            description=f"Redeemed reward: {instance.reward.name}"
        )


def update_leaderboards(user):
    """Update all active leaderboards for a user."""
    from .services import leaderboard_service
    leaderboard_service.update_user_leaderboards(user)


@receiver(post_save, sender=User)
def create_initial_user_level(sender, instance, created, **kwargs):
    """Create initial user level when a user is created."""
    if created:
        # Get the first level
        first_level = Level.objects.order_by('number').first()
        if first_level:
            UserLevel.objects.create(
                user=instance,
                level=first_level,
                total_points=0
            )
            # gamification/signals.py

@receiver(post_save, sender=Point)
def update_user_points(sender, instance, created, **kwargs):
    """Update user's total points when points are added."""
    if created:
        user = instance.user
        
        # Get or create user level
        user_level, created = UserLevel.objects.get_or_create(
            user=user,
            defaults={
                'level': Level.objects.order_by('number').first(),
                'total_points': 0
            }
        )
        
        # Update total points - CORRECTION ICI
        total_points = Point.objects.filter(user=user).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        user_level.total_points = total_points
        user_level.save()
        
        # Check if user should level up
        user_level.update_level()
        
        # Update leaderboards
        update_leaderboards(user)