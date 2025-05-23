# core/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register(r'challenge-types', ChallengeTypeViewSet)
router.register(r'docker-templates', DockerConfigTemplateViewSet, basename='dockerconfigtemplate-view')
router.register(r'docker-config-templates', DockerConfigTemplateCreateViewSet, basename='dockerconfigtemplate-create')
router.register(r'challenges', ChallengeViewSet)
router.register(r'categories', ChallengeCategoryViewSet)



urlpatterns = [
    path('start/<uuid:challenge_id>/', start_challenge, name='start_challenge'),
    path('status/<uuid:instance_id>/', check_status, name='check_status'), 
    path('stop/<uuid:challenge_id>/', stop_challenge, name='stop_challenge'), 
    path('instances/<str:instance_id>/download-key/', download_ssh_key, name='download-ssh-key'),
    path('submit-flag/', submit_flag, name='submit_flag'),
    path('docker-templates/', docker_templates_view, name='docker-templates'),
    path('', include(router.urls)),
]