# notifications/serializers.py
from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    sender_details = UserSerializer(source='sender', read_only=True)
    recipient_details = UserSerializer(source='recipient', read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'recipient_details', 'sender', 'sender_details', 
                  'notification_type', 'content', 'object_id', 'content_type', 
                  'is_read', 'created_at', 'updated_at', 'url', 'image']
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = ['id', 'user', 'user_details', 'notification_type', 'email_enabled', 
                  'push_enabled', 'in_app_enabled', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']