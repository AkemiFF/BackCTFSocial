from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CommentViewSet, ConversationViewSet, MessageViewSet,
                    PostViewSet, ProjectViewSet, SocialInteractionViewSet)

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'interactions', SocialInteractionViewSet, basename='interaction')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'projects', ProjectViewSet, basename='project')

urlpatterns = [
    path('', include(router.urls)),
]