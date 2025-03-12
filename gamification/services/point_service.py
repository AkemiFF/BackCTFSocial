# gamification/services/point_service.py
from ..models import Point, UserLevel


def award_points(user, amount, source, description=""):
    """Award points to a user and update their level."""
    if amount <= 0:
        return None
    
    # Create point record
    point = Point.objects.create(
        user=user,
        amount=amount,
        source=source,
        description=description
    )
    
    return point


def deduct_points(user, amount, source, description=""):
    """Deduct points from a user."""
    if amount <= 0:
        return None
    
    # Create negative point record
    point = Point.objects.create(
        user=user,
        amount=-amount,
        source=source,
        description=description
    )
    
    return point


def get_user_total_points(user):
    """Get total points for a user."""
    try:
        return user.level.total_points
    except UserLevel.DoesNotExist:
        return 0


def get_user_point_history(user, limit=None, source=None):
    """Get point history for a user."""
    query = Point.objects.filter(user=user)
    
    if source:
        query = query.filter(source=source)
    
    query = query.order_by('-created_at')
    
    if limit:
        query = query[:limit]
    
    return query