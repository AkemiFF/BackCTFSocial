# teams/permissions.py
from rest_framework import permissions


class IsTeamMember(permissions.BasePermission):
    """
    Custom permission to only allow members of a team to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow staff and admins
        if request.user.is_staff or request.user.role == 'administrator':
            return True
        
        # Check if the user is a member of the team
        if hasattr(obj, 'team'):
            # For projects, tasks, announcements, etc.
            return obj.team.members.filter(user=request.user).exists()
        
        # For teams
        if hasattr(obj, 'members'):
            return obj.members.filter(user=request.user).exists()
        
        return False


class IsTeamAdmin(permissions.BasePermission):
    """
    Custom permission to only allow team admins or owners to perform certain actions.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow staff and admins
        if request.user.is_staff or request.user.role == 'administrator':
            return True
        
        # Check if the user is an admin or owner of the team
        if hasattr(obj, 'team'):
            # For projects, tasks, announcements, etc.
            return obj.team.members.filter(
                user=request.user,
                role__in=['admin', 'owner']
            ).exists()
        
        # For teams
        if hasattr(obj, 'members'):
            return obj.members.filter(
                user=request.user,
                role__in=['admin', 'owner']
            ).exists()
        
        return False


class IsTeamOwner(permissions.BasePermission):
    """
    Custom permission to only allow team owners to perform certain actions.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow staff and admins
        if request.user.is_staff or request.user.role == 'administrator':
            return True
        
        # Check if the user is an owner of the team
        if hasattr(obj, 'team'):
            # For projects, tasks, announcements, etc.
            return obj.team.members.filter(
                user=request.user,
                role='owner'
            ).exists()
        
        # For teams
        if hasattr(obj, 'members'):
            return obj.members.filter(
                user=request.user,
                role='owner'
            ).exists()
        
        return False


class IsPublicOrTeamMember(permissions.BasePermission):
    """
    Custom permission to allow access to public teams or to team members.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow staff and admins
        if request.user.is_staff or request.user.role == 'administrator':
            return True
        
        # Allow if the team is public and the request is a safe method
        if request.method in permissions.SAFE_METHODS:
            if hasattr(obj, 'is_public') and obj.is_public:
                return True
            
            if hasattr(obj, 'team') and obj.team.is_public:
                return True
        
        # Allow if the user is a member of the team
        if hasattr(obj, 'team'):
            # For projects, tasks, announcements, etc.
            return obj.team.members.filter(user=request.user).exists()
        
        # For teams
        if hasattr(obj, 'members'):
            return obj.members.filter(user=request.user).exists()
        
        return False


class IsInvitationRecipient(permissions.BasePermission):
    """
    Custom permission to only allow the recipient of an invitation to accept or decline it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow staff and admins
        if request.user.is_staff or request.user.role == 'administrator':
            return True
        
        # Check if the user is the invitee
        if hasattr(obj, 'invitee'):
            return obj.invitee == request.user
        
        return False


class IsTaskAssigneeOrTeamAdmin(permissions.BasePermission):
    """
    Custom permission to only allow the assignee of a task or team admins to update it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow staff and admins
        if request.user.is_staff or request.user.role == 'administrator':
            return True
        
        # Allow if the user is the assignee
        if hasattr(obj, 'assigned_to') and obj.assigned_to == request.user:
            return True
        
        # Allow if the user is an admin or owner of the team
        if hasattr(obj, 'project') and hasattr(obj.project, 'team'):
            return obj.project.team.members.filter(
                user=request.user,
                role__in=['admin', 'owner']
            ).exists()
        
        return False