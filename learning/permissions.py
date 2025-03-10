# learning/permissions.py
from rest_framework import permissions


class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow instructors to edit content.
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to instructors
        return request.user.is_authenticated and (
            request.user.role in ['mentor', 'administrator'] or 
            request.user.is_staff
        )


class IsOwnerOrInstructor(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or instructors to view/edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow instructors and admins
        if request.user.role in ['mentor', 'administrator'] or request.user.is_staff:
            return True
        
        # Check if the object has a user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False