# notifications/serializers.py
from accounts.serializers import UserSerializer
from rest_framework import serializers

from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)  # Remplacer 'recipient' par 'user'
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'user_details', 'title', 'message', 
            'notification_type', 'priority', 'is_read', 'created_at', 
            'read_at', 'url', 'related_achievement', 'related_challenge'  # Ajouter les champs réels
        ]

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user', 'user_details', 'email_notifications', 
            'push_notifications', 'achievement_notifications', 
            'challenge_notifications', 'course_notifications', 
            'event_notifications', 'team_notifications', 
            'social_notifications', 'system_notifications'
        ]