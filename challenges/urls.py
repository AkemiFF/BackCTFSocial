# challenges/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (ChallengeCompletionViewSet, ChallengeRatingViewSet,
                    ChallengeViewSet, ResourceViewSet, SubmissionViewSet,
                    UserHintViewSet)

router = DefaultRouter()
router.register(r'challenges', ChallengeViewSet)
router.register(r'resources', ResourceViewSet)
router.register(r'submissions', SubmissionViewSet, basename='submission')
router.register(r'user-hints', UserHintViewSet, basename='user-hint')
router.register(r'ratings', ChallengeRatingViewSet, basename='challenge-rating')
router.register(r'completions', ChallengeCompletionViewSet, basename='challenge-completion')

urlpatterns = [
    path('', include(router.urls)),
]