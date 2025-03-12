# notifications/views.py
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification, NotificationPreference
from .permissions import IsRecipientOrAdmin, IsUserOrAdmin
from .serializers import (NotificationPreferenceSerializer,
                          NotificationSerializer)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsRecipientOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['recipient', 'notification_type', 'is_read']
    ordering_fields = ['created_at', 'updated_at']
    
    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.role == 'administrator':
            return Notification.objects.all()
        
        return Notification.objects.filter(recipient=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Mark a notification as read.
        """
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read', 'updated_at'])
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_unread(self, request, pk=None):
        """
        Mark a notification as unread.
        """
        notification = self.get_object()
        notification.is_read = False
        notification.save(update_fields=['is_read', 'updated_at'])
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """
        Mark all notifications as read.
        """
        # Get unread notifications for the current user
        notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        )
        
        # Filter by notification_type if provided
        notification_type = request.data.get('notification_type')
        if notification_type:
            notifications = notifications.filter(notification_type=notification_type)
        
        # Update all notifications
        count = notifications.count()
        notifications.update(is_read=True, updated_at=timezone.now())
        
        return Response({"detail": f"Marked {count} notifications as read."}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Return the count of unread notifications.
        """
        # Get unread notifications for the current user
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        return Response({"unread_count": count})
    
    @action(detail=False, methods=['get'])
    def my_notifications(self, request):
        """
        Return a list of the current user's notifications.
        """
        notifications = Notification.objects.filter(recipient=request.user)
        
        # Filter by is_read if provided
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            notifications = notifications.filter(is_read=(is_read.lower() == 'true'))
        
        # Filter by notification_type if provided
        notification_type = request.query_params.get('notification_type')
        if notification_type:
            notifications = notifications.filter(notification_type=notification_type)
        
        # Order by created_at (newest first)
        notifications = notifications.order_by('-created_at')
        
        page = self.paginate_queryset(notifications)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['delete'])
    def delete_all_read(self, request):
        """
        Delete all read notifications.
        """
        # Get read notifications for the current user
        notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=True
        )
        
        # Filter by notification_type if provided
        notification_type = request.query_params.get('notification_type')
        if notification_type:
            notifications = notifications.filter(notification_type=notification_type)
        
        # Delete all notifications
        count = notifications.count()
        notifications.delete()
        
        return Response({"detail": f"Deleted {count} read notifications."}, status=status.HTTP_200_OK)


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated, IsUserOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'notification_type']
    
    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.role == 'administrator':
            return NotificationPreference.objects.all()
        
        return NotificationPreference.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """
        Return a list of the current user's notification preferences.
        """
        preferences = NotificationPreference.objects.filter(user=request.user)
        
        # Filter by notification_type if provided
        notification_type = request.query_params.get('notification_type')
        if notification_type:
            preferences = preferences.filter(notification_type=notification_type)
        
        serializer = self.get_serializer(preferences, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def update_preferences(self, request):
        """
        Update multiple notification preferences at once.
        """
        preferences_data = request.data.get('preferences', [])
        if not preferences_data or not isinstance(preferences_data, list):
            return Response(
                {"detail": "Invalid data format. Expected a list of preferences."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_preferences = []
        
        for pref_data in preferences_data:
            notification_type = pref_data.get('notification_type')
            if not notification_type:
                continue
            
            # Get or create the preference
            preference, created = NotificationPreference.objects.get_or_create(
                user=request.user,
                notification_type=notification_type,
                defaults={
                    'email_enabled': pref_data.get('email_enabled', True),
                    'push_enabled': pref_data.get('push_enabled', True),
                    'in_app_enabled': pref_data.get('in_app_enabled', True)
                }
            )
            
            # Update if not created
            if not created:
                if 'email_enabled' in pref_data:
                    preference.email_enabled = pref_data['email_enabled']
                if 'push_enabled' in pref_data:
                    preference.push_enabled = pref_data['push_enabled']
                if 'in_app_enabled' in pref_data:
                    preference.in_app_enabled = pref_data['in_app_enabled']
                
                preference.save()
            
            updated_preferences.append(preference)
        
        serializer = self.get_serializer(updated_preferences, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def toggle_all(self, request):
        """
        Toggle all notification preferences of a specific type.
        """
        channel = request.data.get('channel')  # 'email', 'push', or 'in_app'
        enabled = request.data.get('enabled', True)
        
        if channel not in ['email', 'push', 'in_app']:
            return Response(
                {"detail": "Invalid channel. Must be 'email', 'push', or 'in_app'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all preferences for the current user
        preferences = NotificationPreference.objects.filter(user=request.user)
        
        # Filter by notification_type if provided
        notification_type = request.data.get('notification_type')
        if notification_type:
            preferences = preferences.filter(notification_type=notification_type)
        
        # Update all preferences
        if channel == 'email':
            preferences.update(email_enabled=enabled, updated_at=timezone.now())
        elif channel == 'push':
            preferences.update(push_enabled=enabled, updated_at=timezone.now())
        elif channel == 'in_app':
            preferences.update(in_app_enabled=enabled, updated_at=timezone.now())
        
        serializer = self.get_serializer(preferences, many=True)
        return Response(serializer.data)