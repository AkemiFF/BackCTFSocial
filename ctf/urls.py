# core/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import *

urlpatterns = [
    path('start/<str:challenge_id>/', start_challenge, name='start_challenge'),
]