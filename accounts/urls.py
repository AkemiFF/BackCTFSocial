# accounts/urls.py
import accounts.views as views
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'profiles', UserProfileViewSet)
router.register(r'sessions', UserSessionViewSet, basename='session')

urlpatterns = [
    path('my_profile/', UserProfileDetailsViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'}), name='my-profile'),
    path('', include(router.urls)),
]