# gamification/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (Achievement, Badge, Challenge, Leaderboard,
                     LeaderboardEntry, Level, Point, Reward, UserAchievement,
                     UserBadge, UserChallenge, UserLevel, UserReward)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile_image']


class PointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Point
        fields = ['id', 'user', 'amount', 'source', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ['id', 'number', 'name', 'points_required', 'icon', 'description']
        read_only_fields = ['id']


class UserLevelSerializer(serializers.ModelSerializer):
    level = LevelSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserLevel
        fields = ['id', 'user', 'level', 'total_points', 'points_to_next_level', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['id', 'name', 'description', 'icon', 'category', 'points_value', 'is_hidden']
        read_only_fields = ['id']


class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserBadge
        fields = ['id', 'user', 'badge', 'earned_at']
        read_only_fields = ['id', 'earned_at']


class ChallengeSerializer(serializers.ModelSerializer):
    badge_reward = BadgeSerializer(read_only=True)
    
    class Meta:
        model = Challenge
        fields = [
            'id', 'title', 'description', 'difficulty', 'points_reward', 
            'badge_reward', 'start_date', 'end_date', 'status', 
            'completion_criteria', 'max_completions'
        ]
        read_only_fields = ['id']


class UserChallengeSerializer(serializers.ModelSerializer):
    challenge = ChallengeSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserChallenge
        fields = [
            'id', 'user', 'challenge', 'status', 'progress', 
            'progress_percentage', 'started_at', 'completed_at'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at']


class AchievementSerializer(serializers.ModelSerializer):
    badge_reward = BadgeSerializer(read_only=True)
    
    class Meta:
        model = Achievement
        fields = [
            'id', 'name', 'description', 'icon', 'points_reward', 
            'badge_reward', 'is_hidden', 'criteria'
        ]
        read_only_fields = ['id']


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = ['id', 'user', 'achievement', 'unlocked_at']
        read_only_fields = ['id', 'unlocked_at']


class RewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reward
        fields = [
            'id', 'name', 'description', 'image', 'points_cost', 
            'quantity_available', 'is_active', 'start_date', 
            'end_date', 'redemption_instructions'
        ]
        read_only_fields = ['id']


class UserRewardSerializer(serializers.ModelSerializer):
    reward = RewardSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserReward
        fields = [
            'id', 'user', 'reward', 'points_spent', 'redeemed_at', 
            'status', 'fulfillment_details', 'code'
        ]
        read_only_fields = ['id', 'redeemed_at', 'code']


class LeaderboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leaderboard
        fields = [
            'id', 'name', 'description', 'category', 'period', 
            'start_date', 'end_date', 'is_active'
        ]
        read_only_fields = ['id']


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    leaderboard = LeaderboardSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = LeaderboardEntry
        fields = ['id', 'leaderboard', 'user', 'score', 'rank', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class LeaderboardDetailSerializer(serializers.ModelSerializer):
    entries = serializers.SerializerMethodField()
    
    class Meta:
        model = Leaderboard
        fields = [
            'id', 'name', 'description', 'category', 'period', 
            'start_date', 'end_date', 'is_active', 'entries'
        ]
        read_only_fields = ['id', 'entries']
    
    def get_entries(self, obj):
        # Get top entries
        entries = obj.entries.order_by('rank')[:100]
        return LeaderboardEntrySerializer(entries, many=True).data


class UserGamificationProfileSerializer(serializers.ModelSerializer):
    level = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()
    achievements = serializers.SerializerMethodField()
    challenges = serializers.SerializerMethodField()
    points_history = serializers.SerializerMethodField()
    leaderboard_positions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'level', 'badges', 'achievements', 'challenges', 
            'points_history', 'leaderboard_positions'
        ]
    
    def get_level(self, obj):
        try:
            return UserLevelSerializer(obj.level).data
        except:
            return None
    
    def get_badges(self, obj):
        badges = UserBadge.objects.filter(user=obj)
        return UserBadgeSerializer(badges, many=True).data
    
    def get_achievements(self, obj):
        achievements = UserAchievement.objects.filter(user=obj)
        return UserAchievementSerializer(achievements, many=True).data
    
    def get_challenges(self, obj):
        challenges = UserChallenge.objects.filter(
            user=obj, 
            status='completed'
        )
        return UserChallengeSerializer(challenges, many=True).data
    
    def get_points_history(self, obj):
        # Get recent points history
        points = Point.objects.filter(user=obj).order_by('-created_at')[:10]
        return PointSerializer(points, many=True).data
    
    def get_leaderboard_positions(self, obj):
        # Get user's positions in active leaderboards
        entries = LeaderboardEntry.objects.filter(
            user=obj,
            leaderboard__is_active=True
        )
        return LeaderboardEntrySerializer(entries, many=True).data