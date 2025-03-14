# gamification/views.py
from django.contrib.auth import get_user_model
from django.db import models
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
# Root API view
from rest_framework.views import APIView

from .models import (Achievement, Badge, Challenge, Leaderboard,
                     LeaderboardEntry, Level, Point, Reward, UserAchievement,
                     UserBadge, UserChallenge, UserLevel, UserReward)
from .permissions import IsAdminOrReadOnly
from .serializers import (AchievementSerializer, BadgeSerializer,
                          ChallengeSerializer, LeaderboardDetailSerializer,
                          LeaderboardEntrySerializer, LeaderboardSerializer,
                          LevelSerializer, PointSerializer, RewardSerializer,
                          UserAchievementSerializer, UserBadgeSerializer,
                          UserChallengeSerializer,
                          UserGamificationProfileSerializer,
                          UserLevelSerializer, UserRewardSerializer)
from .services import achievement_service, leaderboard_service, point_service


class PointViewSet(viewsets.ModelViewSet):
    """
    API endpoint for user points.
    """
    queryset = Point.objects.all()
    serializer_class = PointSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'source']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Point.objects.all()
        return Point.objects.filter(user=user)
    
    @action(detail=False, methods=['post'])
    def award(self, request):
        """Award points to a user."""
        if not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        amount = request.data.get('amount')
        source = request.data.get('source', 'admin')
        description = request.data.get('description', '')
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            point = point_service.award_points(
                user=user,
                amount=int(amount),
                source=source,
                description=description
            )
            
            return Response(
                PointSerializer(point).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class LevelViewSet(viewsets.ModelViewSet):
    """
    API endpoint for levels.
    """
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['number']
    ordering_fields = ['number', 'points_required']
    ordering = ['number']


class UserLevelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user levels.
    """
    queryset = UserLevel.objects.all()
    serializer_class = UserLevelSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'level']
    ordering_fields = ['total_points', 'updated_at']
    ordering = ['-total_points']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserLevel.objects.all()
        return UserLevel.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def my_level(self, request):
        """Get the current user's level."""
        try:
            user_level = UserLevel.objects.get(user=request.user)
            return Response(
                UserLevelSerializer(user_level).data
            )
        except UserLevel.DoesNotExist:
            return Response(
                {"detail": "User level not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class BadgeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for badges.
    """
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_hidden']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'points_value']
    ordering = ['name']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Badge.objects.all()
        return Badge.objects.filter(is_hidden=False)


class UserBadgeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user badges.
    """
    queryset = UserBadge.objects.all()
    serializer_class = UserBadgeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'badge']
    ordering_fields = ['earned_at']
    ordering = ['-earned_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserBadge.objects.all()
        return UserBadge.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def my_badges(self, request):
        """Get the current user's badges."""
        badges = UserBadge.objects.filter(user=request.user)
        return Response(
            UserBadgeSerializer(badges, many=True).data
        )
    
    @action(detail=False, methods=['post'])
    def award(self, request):
        """Award a badge to a user."""
        if not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        badge_id = request.data.get('badge_id')
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            badge = Badge.objects.get(id=badge_id)
            
            user_badge, created = UserBadge.objects.get_or_create(
                user=user,
                badge=badge
            )
            
            if not created:
                return Response(
                    {"detail": "User already has this badge."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(
                UserBadgeSerializer(user_badge).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ChallengeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for challenges.
    """
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['difficulty', 'status']
    search_fields = ['title', 'description']
    ordering_fields = ['start_date', 'points_reward']
    ordering = ['-start_date']
    
    def get_queryset(self):
        queryset = Challenge.objects.all()
        
        # Filter by active status
        active = self.request.query_params.get('active')
        if active == 'true':
            now = timezone.now()
            queryset = queryset.filter(
                status='active',
                start_date__lte=now
            ).filter(
                models.Q(end_date__isnull=True) | 
                models.Q(end_date__gt=now)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a challenge."""
        challenge = self.get_object()
        user = request.user
        
        # Check if challenge is active
        if not challenge.is_active:
            return Response(
                {"detail": "This challenge is not active."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already joined
        if UserChallenge.objects.filter(user=user, challenge=challenge).exists():
            return Response(
                {"detail": "You have already joined this challenge."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user challenge
        user_challenge = UserChallenge.objects.create(
            user=user,
            challenge=challenge,
            status='in_progress',
            progress={},
            progress_percentage=0
        )
        
        return Response(
            UserChallengeSerializer(user_challenge).data,
            status=status.HTTP_201_CREATED
        )


class UserChallengeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for user challenges.
    """
    queryset = UserChallenge.objects.all()
    serializer_class = UserChallengeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'challenge', 'status']
    ordering_fields = ['started_at', 'completed_at']
    ordering = ['-started_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserChallenge.objects.all()
        return UserChallenge.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def my_challenges(self, request):
        """Get the current user's challenges."""
        challenges = UserChallenge.objects.filter(user=request.user)
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            challenges = challenges.filter(status=status_filter)
        
        return Response(
            UserChallengeSerializer(challenges, many=True).data
        )
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update progress for a challenge."""
        user_challenge = self.get_object()
        
        # Ensure user owns this challenge
        if user_challenge.user != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to update this challenge."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update progress
        progress_data = request.data.get('progress', {})
        progress_percentage = user_challenge.update_progress(progress_data)
        
        return Response({
            "progress_percentage": progress_percentage,
            "status": user_challenge.status
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a challenge as completed."""
        user_challenge = self.get_object()
        
        # Ensure user owns this challenge or is staff
        if user_challenge.user != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to complete this challenge."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Complete the challenge
        if user_challenge.complete():
            return Response({
                "detail": "Challenge completed successfully.",
                "points_awarded": user_challenge.challenge.points_reward
            })
        else:
            return Response(
                {"detail": "Challenge is already completed."},
                status=status.HTTP_400_BAD_REQUEST
            )


class AchievementViewSet(viewsets.ModelViewSet):
    """
    API endpoint for achievements.
    """
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_hidden']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'points_reward']
    ordering = ['name']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Achievement.objects.all()
        return Achievement.objects.filter(is_hidden=False)


class UserAchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user achievements.
    """
    queryset = UserAchievement.objects.all()
    serializer_class = UserAchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'achievement']
    ordering_fields = ['unlocked_at']
    ordering = ['-unlocked_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserAchievement.objects.all()
        return UserAchievement.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def my_achievements(self, request):
        """Get the current user's achievements."""
        achievements = UserAchievement.objects.filter(user=request.user)
        return Response(
            UserAchievementSerializer(achievements, many=True).data
        )
    
    @action(detail=False, methods=['post'])
    def check_all(self, request):
        user = request.user
        achievement_service.check_all_achievements(user)
        
        # Return updated achievements
        achievements = UserAchievement.objects.filter(user=user)
        return Response(
            UserAchievementSerializer(achievements, many=True).data
        )


class RewardViewSet(viewsets.ModelViewSet):
    """
    API endpoint for rewards.
    """
    queryset = Reward.objects.all()
    serializer_class = RewardSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['points_cost', 'start_date']
    ordering = ['points_cost']
    
    def get_queryset(self):
        queryset = Reward.objects.all()
        
        # Filter by available status
        available = self.request.query_params.get('available')
        if available == 'true':
            now = timezone.now()
            queryset = queryset.filter(
                is_active=True,
                start_date__lte=now
            ).filter(
                models.Q(end_date__isnull=True) | 
                models.Q(end_date__gt=now)
            ).exclude(
                quantity_available=0
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def redeem(self, request, pk=None):
        """Redeem a reward."""
        reward = self.get_object()
        user = request.user
        
        # Check if reward is available
        if not reward.is_available:
            return Response(
                {"detail": "This reward is not available."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user has enough points
        user_points = point_service.get_user_total_points(user)
        if user_points < reward.points_cost:
            return Response(
                {"detail": f"You don't have enough points. Required: {reward.points_cost}, Available: {user_points}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user reward
        user_reward = UserReward.objects.create(
            user=user,
            reward=reward,
            points_spent=reward.points_cost,
            status='pending'
        )
        
        # Update reward quantity
        if reward.quantity_available > 0:
            reward.quantity_available -= 1
            reward.save()
        
        return Response(
            UserRewardSerializer(user_reward).data,
            status=status.HTTP_201_CREATED
        )


class UserRewardViewSet(viewsets.ModelViewSet):
    """
    API endpoint for user rewards.
    """
    queryset = UserReward.objects.all()
    serializer_class = UserRewardSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'reward', 'status']
    ordering_fields = ['redeemed_at']
    ordering = ['-redeemed_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserReward.objects.all()
        return UserReward.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def my_rewards(self, request):
        """Get the current user's rewards."""
        rewards = UserReward.objects.filter(user=request.user)
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            rewards = rewards.filter(status=status_filter)
        
        return Response(
            UserRewardSerializer(rewards, many=True).data
        )
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update the status of a reward redemption."""
        if not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_reward = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(UserReward.STATUS_CHOICES):
            return Response(
                {"detail": f"Invalid status. Choices are: {dict(UserReward.STATUS_CHOICES).keys()}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_reward.status = new_status
        user_reward.save()
        
        return Response(
            UserRewardSerializer(user_reward).data
        )


class LeaderboardViewSet(viewsets.ModelViewSet):
    """
    API endpoint for leaderboards.
    """
    queryset = Leaderboard.objects.all()
    serializer_class = LeaderboardSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['category', 'period', 'is_active']
    ordering_fields = ['start_date']
    ordering = ['-start_date']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LeaderboardDetailSerializer
        return LeaderboardSerializer
    
    @action(detail=False, methods=['post'])
    def create_periodic(self, request):
        """Create periodic leaderboards."""
        if not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        leaderboard_service.create_periodic_leaderboards()
        return Response({"detail": "Periodic leaderboards created successfully."})


class LeaderboardEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for leaderboard entries.
    """
    queryset = LeaderboardEntry.objects.all()
    serializer_class = LeaderboardEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['leaderboard', 'user']
    ordering_fields = ['rank', 'score']
    ordering = ['rank']
    
    @action(detail=False, methods=['get'])
    def my_positions(self, request):
        """Get the current user's positions in leaderboards."""
        entries = LeaderboardEntry.objects.filter(
            user=request.user,
            leaderboard__is_active=True
        )
        
        # Filter by category
        category = request.query_params.get('category')
        if category:
            entries = entries.filter(leaderboard__category=category)
        
        # Filter by period
        period = request.query_params.get('period')
        if period:
            entries = entries.filter(leaderboard__period=period)
        
        return Response(
            LeaderboardEntrySerializer(entries, many=True).data
        )


class UserGamificationProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user gamification profiles.
    """
    queryset = get_user_model().objects.all()
    serializer_class = UserGamificationProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return get_user_model().objects.all()
        return get_user_model().objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get the current user's gamification profile."""
        return Response(
            UserGamificationProfileSerializer(request.user).data
        )


class GamificationAPIRootView(APIView):
    """
    Root view for the Gamification API.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, format=None):
        return Response({
            'points': request.build_absolute_uri(reverse('point-list')),
            'levels': request.build_absolute_uri(reverse('level-list')),
            'user-levels': request.build_absolute_uri(reverse('userlevel-list')),
            'badges': request.build_absolute_uri(reverse('badge-list')),
            'user-badges': request.build_absolute_uri(reverse('userbadge-list')),
            'challenges': request.build_absolute_uri(reverse('challenge-list')),
            'user-challenges': request.build_absolute_uri(reverse('userchallenge-list')),
            'achievements': request.build_absolute_uri(reverse('achievement-list')),
            'user-achievements': request.build_absolute_uri(reverse('userachievement-list')),
            'rewards': request.build_absolute_uri(reverse('reward-list')),
            'user-rewards': request.build_absolute_uri(reverse('userreward-list')),
            'leaderboards': request.build_absolute_uri(reverse('leaderboard-list')),
            'leaderboard-entries': request.build_absolute_uri(reverse('leaderboardentry-list')),
            'user-profiles': request.build_absolute_uri(reverse('usergamificationprofile-list')),
            'my-profile': request.build_absolute_uri(reverse('usergamificationprofile-my-profile')),
        })