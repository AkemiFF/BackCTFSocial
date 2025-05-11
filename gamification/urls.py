# gamification/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (AchievementViewSet, BadgeViewSet, ChallengeViewSet,
                    GamificationAPIRootView, LeaderboardEntryViewSet,
                    LevelViewSet, PointViewSet, RewardViewSet,
                    UserAchievementViewSet, UserBadgeViewSet,
                    UserChallengeViewSet, UserGamificationProfileViewSet,
                    UserLevelViewSet, UserRewardViewSet)

router = DefaultRouter()
router.register(r'points', PointViewSet, basename='point')
router.register(r'levels', LevelViewSet, basename='level')
router.register(r'user-levels', UserLevelViewSet, basename='userlevel')
router.register(r'badges', BadgeViewSet, basename='badge')
router.register(r'user-badges', UserBadgeViewSet, basename='userbadge')
router.register(r'challenges', ChallengeViewSet, basename='challenge')
router.register(r'user-challenges', UserChallengeViewSet, basename='userchallenge')
router.register(r'achievements', AchievementViewSet, basename='achievement')
router.register(r'user-achievements', UserAchievementViewSet, basename='userachievement')
router.register(r'rewards', RewardViewSet, basename='reward')
router.register(r'user-rewards', UserRewardViewSet, basename='userreward')
router.register(r'leaderboard-entries', LeaderboardEntryViewSet, basename='leaderboardentry')
router.register(r'user-profiles', UserGamificationProfileViewSet, basename='usergamificationprofile')

urlpatterns = [
    path('', GamificationAPIRootView.as_view(), name='gamification-api-root'),
    path('', include(router.urls)),
]