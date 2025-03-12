# api/permissions.py
from rest_framework import permissions


class IsApiUser(permissions.BasePermission):
    """
    Permission to only allow users with API access.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.has_api_access)


class HasApiScope(permissions.BasePermission):
    """
    Permission to check if user has the required API scope.
    """
    def __init__(self, required_scope):
        self.required_scope = required_scope
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has the required scope
        try:
            from accounts.models import ApiScope
            user_scopes = ApiScope.objects.filter(user=request.user, is_active=True)
            return user_scopes.filter(scope=self.required_scope).exists()
        except:
            return False