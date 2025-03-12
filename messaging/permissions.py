# messaging/permissions.py
from rest_framework import permissions


class IsChannelMember(permissions.BasePermission):
    """
    Custom permission to only allow members of a channel to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow staff and admins
        if request.user.is_staff or request.user.role == 'administrator':
            return True
        
        # Check if the user is a member of the channel
        if hasattr(obj, 'channel'):
            # For messages, read receipts, etc.
            return obj.channel.members.filter(user=request.user).exists()
        
        # For channels
        if hasattr(obj, 'members'):
            return obj.members.filter(user=request.user).exists()
        
        return False


class IsChannelAdmin(permissions.BasePermission):
    """
    Custom permission to only allow channel admins to perform certain actions.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow staff and admins
        if request.user.is_staff or request.user.role == 'administrator':
            return True
        
        # Check if the user is an admin of the channel
        if hasattr(obj, 'channel'):
            # For messages, read receipts, etc.
            return obj.channel.members.filter(user=request.user, role='admin').exists()
        
        # For channels
        if hasattr(obj, 'members'):
            return obj.members.filter(user=request.user, role='admin').exists()
        
        return False


class IsMessageSender(permissions.BasePermission):
    """
    Custom permission to only allow the sender of a message to edit or delete it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow staff and admins
        if request.user.is_staff or request.user.role == 'administrator':
            return True
        
        # Check if the user is the sender of the message
        if hasattr(obj, 'sender'):
            return obj.sender == request.user
        
        return False