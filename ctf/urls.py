# core/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register(r'challenge-types', ChallengeTypeViewSet)
router.register(r'docker-templates', DockerConfigTemplateViewSet)
router.register(r'challenges', ChallengeViewSet)
router.register(r'categories', ChallengeCategoryViewSet)



urlpatterns = [
    path('start/<uuid:challenge_id>/', start_challenge, name='start_challenge'),
    path('status/<uuid:instance_id>/', check_status, name='check_status'), 
    path('instances/<str:instance_id>/download-key/', download_ssh_key, name='download-ssh-key'),
    path('docker-templates/', docker_templates_view, name='docker-templates'),
    path('', include(router.urls)),
]