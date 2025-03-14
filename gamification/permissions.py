# gamification/permissions.py
from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to admin users
        return request.user and request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to view or edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Check if user is admin
        if request.user and request.user.is_staff:
            return True
        
        # Check if object has a user field that matches the request user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False