# challenges/permissions.py
from rest_framework import permissions


class IsChallengeCreatorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow creators of a challenge to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the creator or staff
        return obj.created_by == request.user or request.user.is_staff or request.user.role in ['administrator', 'moderator']


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or staff to view/edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow staff and admins
        if request.user.is_staff or request.user.role in ['administrator', 'moderator']:
            return True
        
        # Check if the object has a user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False