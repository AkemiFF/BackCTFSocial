# gamification/tasks.py
from django.utils import timezone

from .models import Leaderboard, LeaderboardEntry
from .services import leaderboard_service


def create_periodic_leaderboards_task():
    """
    Task to create periodic leaderboards.
    Should be run daily.
    """
    leaderboard_service.create_periodic_leaderboards()


def update_leaderboard_ranks_task():
    """
    Task to update ranks for all active leaderboards.
    Should be run hourly.
    """
    active_leaderboards = Leaderboard.objects.filter(is_active=True)
    for leaderboard in active_leaderboards:
        leaderboard_service.update_leaderboard_ranks(leaderboard)


def close_expired_leaderboards_task():
    """
    Task to close expired leaderboards.
    Should be run daily.
    """
    now = timezone.now()
    expired_leaderboards = Leaderboard.objects.filter(
        is_active=True,
        end_date__lt=now
    )
    
    for leaderboard in expired_leaderboards:
        leaderboard.is_active = False
        leaderboard.save()