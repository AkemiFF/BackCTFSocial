# teams/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (TeamAnnouncementViewSet, TeamInvitationViewSet,
                    TeamMemberViewSet, TeamProjectViewSet, TeamTaskViewSet,
                    TeamViewSet)

router = DefaultRouter()
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'members', TeamMemberViewSet, basename='team-member')
router.register(r'invitations', TeamInvitationViewSet, basename='team-invitation')
router.register(r'projects', TeamProjectViewSet, basename='team-project')
router.register(r'tasks', TeamTaskViewSet, basename='team-task')
router.register(r'announcements', TeamAnnouncementViewSet, basename='team-announcement')

# Nested routes
team_projects_router = DefaultRouter()
team_projects_router.register(r'projects', TeamProjectViewSet, basename='team-project')

project_tasks_router = DefaultRouter()
project_tasks_router.register(r'tasks', TeamTaskViewSet, basename='project-task')

team_announcements_router = DefaultRouter()
team_announcements_router.register(r'announcements', TeamAnnouncementViewSet, basename='team-announcement')

urlpatterns = [
    path('', include(router.urls)),
    # Nested routes
    path('teams/<slug:team_slug>/', include(team_projects_router.urls)),
    path('teams/<slug:team_slug>/projects/<slug:project_slug>/', include(project_tasks_router.urls)),
    path('teams/<slug:team_slug>/', include(team_announcements_router.urls)),
]