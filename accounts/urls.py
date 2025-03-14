# accounts/urls.py
import accounts.views as views
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UserProfileViewSet, UserSessionViewSet, UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'profiles', UserProfileViewSet)
router.register(r'sessions', UserSessionViewSet, basename='session')

urlpatterns = [
    path('', include(router.urls)),
]