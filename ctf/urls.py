# core/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register(r'challenges', ChallengeViewSet, basename='challenge')

urlpatterns = [
    path('start/<uuid:challenge_id>/', start_challenge, name='start_challenge'),
    path('status/<uuid:instance_id>/', check_status, name='check_status'), 
    path('instances/<str:instance_id>/download-key/', download_ssh_key, name='download-ssh-key'),
    path('', include(router.urls)),
]