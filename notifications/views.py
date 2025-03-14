# notifications/views.py
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification, NotificationPreference
from .permissions import IsUserOrAdmin
from .serializers import (NotificationPreferenceSerializer,
                          NotificationSerializer)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsUserOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'notification_type', 'is_read']
    ordering_fields = ['created_at', 'updated_at']
    
    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.role == 'administrator':
            return Notification.objects.all()
        
        return Notification.objects.filter(user=self.request.user)
    
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
            user=request.user,
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
            user=request.user,
            is_read=False
        ).count()
        
        return Response({"unread_count": count})
    
    @action(detail=False, methods=['get'])
    def my_notifications(self, request):
        """
        Return a list of the current user's notifications.
        """
        notifications = Notification.objects.filter(user=request.user)
        
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
            user=request.user,
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
    filterset_fields = ['user']  # Retiré 'notification_type' (n'existe pas dans le modèle)
    
    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.role == 'administrator':
            return NotificationPreference.objects.all()
        return NotificationPreference.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """
        Return the current user's notification preferences (un seul objet).
        """
        preference = NotificationPreference.objects.get(user=request.user)
        serializer = self.get_serializer(preference)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def update_preferences(self, request):
        """
        Update notification preferences for the current user.
        """
        # Récupère l'instance existante (pas de création multiple)
        preference = NotificationPreference.objects.get(user=request.user)
        
        # Met à jour les champs booléens en fonction des données reçues
        for field in request.data:
            if hasattr(preference, field):
                setattr(preference, field, request.data[field])
        
        preference.save()
        serializer = self.get_serializer(preference)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def toggle_all(self, request):
        """
        Toggle all notification types for a specific channel (email/push).
        """
        channel = request.data.get('channel')  # 'email' ou 'push'
        enabled = request.data.get('enabled', True)
        
        if channel not in ['email', 'push']:
            return Response(
                {"detail": "Invalid channel. Must be 'email' or 'push'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        preference = NotificationPreference.objects.get(user=request.user)
        
        # Liste des champs à mettre à jour selon le canal
        fields_to_update = {
            'email': ['email_notifications'],
            'push': ['push_notifications']
        }.get(channel, [])
        
        for field in fields_to_update:
            setattr(preference, field, enabled)
        
        preference.save()
        serializer = self.get_serializer(preference)
        return Response(serializer.data)