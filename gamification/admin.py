# gamification/admin.py
from django.contrib import admin

from .models import (Achievement, Badge, Challenge, Leaderboard,
                     LeaderboardEntry, Level, LevelUpEvent, Point, Reward,
                     UserAchievement, UserBadge, UserChallenge, UserLevel,
                     UserReward)


@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'source', 'created_at')
    list_filter = ('source', 'created_at')
    search_fields = ('user__username', 'description')
    date_hierarchy = 'created_at'


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'points_required')
    list_filter = ('number',)
    search_fields = ('name', 'description')
    ordering = ('number',)


@admin.register(UserLevel)
class UserLevelAdmin(admin.ModelAdmin):
    list_display = ('user', 'level', 'total_points', 'points_to_next_level', 'updated_at')
    list_filter = ('level',)
    search_fields = ('user__username',)
    date_hierarchy = 'updated_at'


@admin.register(LevelUpEvent)
class LevelUpEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'from_level', 'to_level', 'created_at')
    list_filter = ('from_level', 'to_level', 'created_at')
    search_fields = ('user__username',)
    date_hierarchy = 'created_at'


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'points_value', 'is_hidden')
    list_filter = ('category', 'is_hidden')
    search_fields = ('name', 'description')


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'earned_at')
    list_filter = ('badge', 'earned_at')
    search_fields = ('user__username', 'badge__name')
    date_hierarchy = 'earned_at'


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'difficulty', 'points_reward', 'status', 'start_date', 'end_date')
    list_filter = ('difficulty', 'status', 'start_date')
    search_fields = ('title', 'description')
    date_hierarchy = 'start_date'


@admin.register(UserChallenge)
class UserChallengeAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'status', 'progress_percentage', 'started_at', 'completed_at')
    list_filter = ('status', 'started_at', 'completed_at')
    search_fields = ('user__username', 'challenge__title')
    date_hierarchy = 'started_at'


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'points_reward', 'is_hidden')
    list_filter = ('is_hidden',)
    search_fields = ('name', 'description')


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'unlocked_at')
    list_filter = ('achievement', 'unlocked_at')
    search_fields = ('user__username', 'achievement__name')
    date_hierarchy = 'unlocked_at'


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ('name', 'points_cost', 'quantity_available', 'is_active', 'start_date', 'end_date')
    list_filter = ('is_active', 'start_date')
    search_fields = ('name', 'description')
    date_hierarchy = 'start_date'


@admin.register(UserReward)
class UserRewardAdmin(admin.ModelAdmin):
    list_display = ('user', 'reward', 'points_spent', 'status', 'redeemed_at')
    list_filter = ('status', 'redeemed_at')
    search_fields = ('user__username', 'reward__name', 'code')
    date_hierarchy = 'redeemed_at'


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'period', 'is_active', 'start_date', 'end_date')
    list_filter = ('category', 'period', 'is_active')
    search_fields = ('name', 'description')
    date_hierarchy = 'start_date'


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = ('leaderboard', 'user', 'score', 'rank', 'updated_at')
    list_filter = ('leaderboard', 'rank')
    search_fields = ('user__username',)
    date_hierarchy = 'updated_at'