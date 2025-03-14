# notifications/permissions.py
from rest_framework import permissions


class IsUserOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow recipients of a notification to view or edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow administrators
        if request.user.is_staff or request.user.role == 'administrator':
            return True
        
        # Check if the user is the recipient
        if hasattr(obj, 'recipient'):
            return obj.recipient == request.user
        
        return False


class IsUserOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow users to view or edit their own preferences.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow administrators
        if request.user.is_staff or request.user.role == 'administrator':
            return True
        
        # Check if the user is the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False