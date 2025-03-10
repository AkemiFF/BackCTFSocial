# core/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (AuditViewSet, CategoryViewSet, FeedbackViewSet,
                    SettingViewSet, SkillViewSet, TagViewSet)

router = DefaultRouter()
router.register(r'tags', TagViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'skills', SkillViewSet)
router.register(r'settings', SettingViewSet, basename='setting')
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'audit', AuditViewSet, basename='audit')

urlpatterns = [
    path('', include(router.urls)),
]