# social/permissions.py
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsParticipantOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow participants of a conversation to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow staff and admins
        if request.user.is_staff or request.user.role == 'administrator':
            return True
        
        # Check if the user is a participant
        if hasattr(obj, 'participants'):
            return request.user in obj.participants.all()
        
        # For messages, check if the user is a participant in the conversation
        if hasattr(obj, 'conversation'):
            return request.user in obj.conversation.participants.all()
        
        return False


class IsPublicOrOwner(permissions.BasePermission):
    """
    Custom permission to allow access to public content or to the owner.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow staff and admins
        if request.user.is_staff or request.user.role == 'administrator':
            return True
        
        # Allow if the content is public
        if hasattr(obj, 'is_public') and obj.is_public:
            return True
        
        # Allow if the user is the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False