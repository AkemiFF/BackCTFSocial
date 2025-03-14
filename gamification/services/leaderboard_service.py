# gamification/services/leaderboard_service.py
from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from ..models import Leaderboard, LeaderboardEntry, Point


def get_date_range_for_period(period):
    """Get start and end dates for a leaderboard period."""
    now = timezone.now()
    
    if period == 'daily':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif period == 'weekly':
        # Start from Monday
        start_date = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_date = start_date + timedelta(days=7)
    elif period == 'monthly':
        # Start from first day of month
        start_date = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        # Go to next month
        if now.month == 12:
            end_date = now.replace(
                year=now.year + 1, month=1, day=1,
                hour=0, minute=0, second=0, microsecond=0
            )
        else:
            end_date = now.replace(
                month=now.month + 1, day=1,
                hour=0, minute=0, second=0, microsecond=0
            )
    elif period == 'yearly':
        start_date = now.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        end_date = now.replace(
            year=now.year + 1, month=1, day=1,
            hour=0, minute=0, second=0, microsecond=0
        )
    else:  # all_time
        start_date = None
        end_date = None
    
    return start_date, end_date


def create_periodic_leaderboards():
    """Create leaderboards for current periods if they don't exist."""
    categories = ['points', 'challenges', 'badges']
    periods = ['daily', 'weekly', 'monthly', 'yearly']
    
    for category in categories:
        for period in periods:
            start_date, end_date = get_date_range_for_period(period)
            
            # Check if leaderboard already exists
            existing = Leaderboard.objects.filter(
                category=category,
                period=period,
                start_date=start_date
            ).exists()
            
            if not existing:
                name = f"{category.capitalize()} {period.capitalize()}"
                Leaderboard.objects.create(
                    name=name,
                    description=f"Leaderboard for {category} earned during this {period} period",
                    category=category,
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=True
                )


def update_user_leaderboards(user):
    """Update all active leaderboards for a user."""
    # Get all active leaderboards
    active_leaderboards = Leaderboard.objects.filter(is_active=True)
    
    for leaderboard in active_leaderboards:
        # Calculate score based on category and period
        score = calculate_user_score(
            user, 
            leaderboard.category, 
            leaderboard.start_date, 
            leaderboard.end_date
        )
        
        # Update or create leaderboard entry
        entry, created = LeaderboardEntry.objects.update_or_create(
            leaderboard=leaderboard,
            user=user,
            defaults={'score': score}
        )
        
        # Update ranks for this leaderboard
        update_leaderboard_ranks(leaderboard)


def calculate_user_score(user, category, start_date=None, end_date=None):
    """Calculate user score for a specific category and time period."""
    if category == 'points':
        # Sum points in the given period
        query = Point.objects.filter(user=user, amount__gt=0)
        if start_date:
            query = query.filter(created_at__gte=start_date)
        if end_date:
            query = query.filter(created_at__lt=end_date)
        
        return query.aggregate(total=Sum('amount'))['total'] or 0
    
    elif category == 'challenges':
        # Count completed challenges in the given period
        from ..models import UserChallenge
        query = UserChallenge.objects.filter(
            user=user, 
            status='completed'
        )
        if start_date:
            query = query.filter(completed_at__gte=start_date)
        if end_date:
            query = query.filter(completed_at__lt=end_date)
        
        return query.count()
    
    elif category == 'badges':
        # Count badges earned in the given period
        from ..models import UserBadge
        query = UserBadge.objects.filter(user=user)
        if start_date:
            query = query.filter(earned_at__gte=start_date)
        if end_date:
            query = query.filter(earned_at__lt=end_date)
        
        return query.count()
    
    return 0


def update_leaderboard_ranks(leaderboard):
    """Update ranks for all entries in a leaderboard."""
    # Get all entries ordered by score
    entries = LeaderboardEntry.objects.filter(
        leaderboard=leaderboard
    ).order_by('-score')
    
    # Update ranks
    current_rank = 1
    previous_score = None
    
    for i, entry in enumerate(entries):
        # If score is the same as previous, assign the same rank
        if previous_score is not None and entry.score == previous_score:
            entry.rank = current_rank
        else:
            entry.rank = i + 1
            current_rank = i + 1
        
        previous_score = entry.score
        entry.save(update_fields=['rank'])