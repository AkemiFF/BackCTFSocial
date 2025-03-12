# gamification/services/achievement_service.py
from django.db.models import Count

from ..models import Achievement, UserAchievement, UserBadge, UserChallenge


def check_level_achievements(user, level):
    """Check if user has unlocked any level-based achievements."""
    # Find achievements that require reaching a certain level
    level_achievements = Achievement.objects.filter(
        criteria__has_key='min_level',
    )
    
    for achievement in level_achievements:
        # Skip if already unlocked
        if UserAchievement.objects.filter(user=user, achievement=achievement).exists():
            continue
        
        min_level = achievement.criteria.get('min_level')
        if level.number >= min_level:
            UserAchievement.objects.create(
                user=user,
                achievement=achievement
            )


def check_badge_achievements(user):
    """Check if user has unlocked any badge-based achievements."""
    # Count user badges
    badge_count = UserBadge.objects.filter(user=user).count()
    
    # Find achievements that require collecting badges
    badge_achievements = Achievement.objects.filter(
        criteria__has_key='badges_count',
    )
    
    for achievement in badge_achievements:
        # Skip if already unlocked
        if UserAchievement.objects.filter(user=user, achievement=achievement).exists():
            continue
        
        required_count = achievement.criteria.get('badges_count')
        if badge_count >= required_count:
            UserAchievement.objects.create(
                user=user,
                achievement=achievement
            )


def check_challenge_achievements(user):
    """Check if user has unlocked any challenge-based achievements."""
    # Count completed challenges
    completed_challenges = UserChallenge.objects.filter(
        user=user, 
        status='completed'
    ).count()
    
    # Find achievements that require completing challenges
    challenge_achievements = Achievement.objects.filter(
        criteria__has_key='challenges_completed',
    )
    
    for achievement in challenge_achievements:
        # Skip if already unlocked
        if UserAchievement.objects.filter(user=user, achievement=achievement).exists():
            continue
        
        required_count = achievement.criteria.get('challenges_completed')
        if completed_challenges >= required_count:
            UserAchievement.objects.create(
                user=user,
                achievement=achievement
            )


def check_all_achievements(user):
    """Check all possible achievements for a user."""
    # Get user level
    try:
        user_level = user.level
        check_level_achievements(user, user_level.level)
    except:
        pass
    
    check_badge_achievements(user)
    check_challenge_achievements(user)