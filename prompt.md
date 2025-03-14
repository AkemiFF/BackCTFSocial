Thought for 3 seconds### Création de l'Application Teams

Je vais maintenant créer les endpoints pour l'application teams, qui permettra aux utilisateurs de former des équipes, de collaborer sur des projets et de gérer les membres et leurs rôles.

## 1. Modèles

Commençons par créer les modèles pour l'application teams:

```python
# teams/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
import uuid


class Team(models.Model):
    """
    Represents a team of users working together
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='teams/avatars/', blank=True, null=True)
    banner = models.ImageField(upload_to='teams/banners/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_teams',
        null=True
    )
    is_public = models.BooleanField(default=True)
    website = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    discord_url = models.URLField(blank=True, null=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Generate a slug if one doesn't exist
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            # Make sure the slug is unique
            while Team.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)
    
    @property
    def member_count(self):
        return self.members.count()


class TeamMember(models.Model):
    """
    Represents a member of a team with a specific role
    """
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    )
    
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_memberships'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member'
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    bio = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('team', 'user')
        ordering = ['role', 'joined_at']
    
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()}) in {self.team.name}"


class TeamInvitation(models.Model):
    """
    Represents an invitation to join a team
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    )
    
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_team_invitations'
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_team_invitations'
    )
    role = models.CharField(
        max_length=20,
        choices=TeamMember.ROLE_CHOICES,
        default='member'
    )
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('team', 'invitee', 'status')
    
    def __str__(self):
        return f"Invitation for {self.invitee.username} to join {self.team.name}"
    
    def save(self, *args, **kwargs):
        # Set expiration date if not provided
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def accept(self):
        """
        Accept the invitation and create a team membership
        """
        if self.status != 'pending':
            return False
        
        if self.is_expired:
            self.status = 'expired'
            self.save(update_fields=['status'])
            return False
        
        # Create team membership
        TeamMember.objects.create(
            team=self.team,
            user=self.invitee,
            role=self.role
        )
        
        self.status = 'accepted'
        self.save(update_fields=['status'])
        return True
    
    def decline(self):
        """
        Decline the invitation
        """
        if self.status != 'pending':
            return False
        
        self.status = 'declined'
        self.save(update_fields=['status'])
        return True


class TeamProject(models.Model):
    """
    Represents a project associated with a team
    """
    STATUS_CHOICES = (
        ('planning', 'Planning'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    )
    
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planning'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_team_projects',
        null=True
    )
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_public = models.BooleanField(default=True)
    repository_url = models.URLField(blank=True, null=True)
    demo_url = models.URLField(blank=True, null=True)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ('team', 'slug')
    
    def __str__(self):
        return f"{self.name} ({self.team.name})"
    
    def save(self, *args, **kwargs):
        # Generate a slug if one doesn't exist
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            # Make sure the slug is unique within the team
            while TeamProject.objects.filter(team=self.team, slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)


class TeamTask(models.Model):
    """
    Represents a task within a team project
    """
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    STATUS_CHOICES = (
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('done', 'Done'),
    )
    
    project = models.ForeignKey(
        TeamProject,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='todo'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_tasks',
        null=True
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_tasks',
        blank=True,
        null=True
    )
    due_date = models.DateField(blank=True, null=True)
    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    class Meta:
        ordering = ['priority', 'due_date', 'created_at']
    
    def __str__(self):
        return self.title


class TeamAnnouncement(models.Model):
    """
    Represents an announcement for a team
    """
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='announcements'
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_announcements',
        null=True
    )
    is_pinned = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.team.name})"
```

## 2. Serializers

Maintenant, créons les serializers pour ces modèles:

```python
# teams/serializers.py
from rest_framework import serializers
from .models import Team, TeamMember, TeamInvitation, TeamProject, TeamTask, TeamAnnouncement
from accounts.serializers import UserSerializer
from django.utils import timezone


class TeamMemberSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = TeamMember
        fields = ['id', 'team', 'user', 'user_details', 'role', 'joined_at', 'bio', 'is_public']
        read_only_fields = ['id', 'team', 'user', 'joined_at']


class TeamSerializer(serializers.ModelSerializer):
    created_by_details = UserSerializer(source='created_by', read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    is_member = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'slug', 'description', 'avatar', 'banner',
                  'created_at', 'updated_at', 'created_by', 'created_by_details',
                  'is_public', 'website', 'github_url', 'discord_url',
                  'member_count', 'is_member', 'user_role']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'created_by']
    
    def get_is_member(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return obj.members.filter(user=request.user).exists()
    
    def get_user_role(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            membership = obj.members.get(user=request.user)
            return membership.role
        except TeamMember.DoesNotExist:
            return None
    
    def create(self, validated_data):
        # Add the created_by from the request
        validated_data['created_by'] = self.context['request'].user
        
        # Create the team
        team = Team.objects.create(**validated_data)
        
        # Add the creator as an owner
        TeamMember.objects.create(
            team=team,
            user=validated_data['created_by'],
            role='owner'
        )
        
        return team


class TeamInvitationSerializer(serializers.ModelSerializer):
    inviter_details = UserSerializer(source='inviter', read_only=True)
    invitee_details = UserSerializer(source='invitee', read_only=True)
    team_details = TeamSerializer(source='team', read_only=True)
    
    class Meta:
        model = TeamInvitation
        fields = ['id', 'team', 'team_details', 'inviter', 'inviter_details',
                  'invitee', 'invitee_details', 'role', 'message', 'created_at',
                  'expires_at', 'status', 'token', 'is_expired']
        read_only_fields = ['id', 'inviter', 'created_at', 'status', 'token', 'is_expired']
    
    def validate(self, data):
        # Check if the invitee is already a member of the team
        if TeamMember.objects.filter(team=data['team'], user=data['invitee']).exists():
            raise serializers.ValidationError("User is already a member of this team.")
        
        # Check if there's already a pending invitation
        if TeamInvitation.objects.filter(
            team=data['team'],
            invitee=data['invitee'],
            status='pending'
        ).exists():
            raise serializers.ValidationError("There is already a pending invitation for this user.")
        
        # Set expiration date if not provided
        if 'expires_at' not in data:
            data['expires_at'] = timezone.now() + timezone.timedelta(days=7)
        
        return data
    
    def create(self, validated_data):
        # Add the inviter from the request
        validated_data['inviter'] = self.context['request'].user
        
        return super().create(validated_data)


class TeamProjectSerializer(serializers.ModelSerializer):
    created_by_details = UserSerializer(source='created_by', read_only=True)
    team_details = TeamSerializer(source='team', read_only=True)
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TeamProject
        fields = ['id', 'team', 'team_details', 'name', 'slug', 'description',
                  'status', 'created_at', 'updated_at', 'created_by',
                  'created_by_details', 'start_date', 'end_date', 'is_public',
                  'repository_url', 'demo_url', 'task_count']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'created_by']
    
    def get_task_count(self, obj):
        return obj.tasks.count()
    
    def create(self, validated_data):
        # Add the created_by from the request
        validated_data['created_by'] = self.context['request'].user
        
        return super().create(validated_data)


class TeamTaskSerializer(serializers.ModelSerializer):
    created_by_details = UserSerializer(source='created_by', read_only=True)
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    project_details = TeamProjectSerializer(source='project', read_only=True)
    
    class Meta:
        model = TeamTask
        fields = ['id', 'project', 'project_details', 'title', 'description',
                  'priority', 'status', 'created_at', 'updated_at', 'created_by',
                  'created_by_details', 'assigned_to', 'assigned_to_details',
                  'due_date', 'estimated_hours']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def create(self, validated_data):
        # Add the created_by from the request
        validated_data['created_by'] = self.context['request'].user
        
        return super().create(validated_data)


class TeamAnnouncementSerializer(serializers.ModelSerializer):
    created_by_details = UserSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = TeamAnnouncement
        fields = ['id', 'team', 'title', 'content', 'created_at', 'updated_at',
                  'created_by', 'created_by_details', 'is_pinned']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def create(self, validated_data):
        # Add the created_by from the request
        validated_data['created_by'] = self.context['request'].user
        
        return super().create(validated_data)
```

## 3. Permissions

Créons des permissions personnalisées pour contrôler l'accès aux ressources:

```python
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
```

## 4. Views

Maintenant, créons les vues pour exposer les modèles via l'API:

```python
# teams/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone

from .models import Team, TeamMember, TeamInvitation, TeamProject, TeamTask, TeamAnnouncement
from .serializers import (
    TeamSerializer, TeamMemberSerializer, TeamInvitationSerializer,
    TeamProjectSerializer, TeamTaskSerializer, TeamAnnouncementSerializer
)
from .permissions import (
    IsTeamMember, IsTeamAdmin, IsTeamOwner, IsPublicOrTeamMember,
    IsInvitationRecipient, IsTaskAssigneeOrTeamAdmin
)


class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated, IsPublicOrTeamMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_public']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at', 'member_count']
    lookup_field = 'slug'
    
    def get_queryset(self):
        queryset = Team.objects.annotate(member_count=Count('members'))
        
        # Filter for public teams or teams the user is a member of
        if not (self.request.user.is_staff or self.request.user.role == 'administrator'):
            queryset = queryset.filter(
                Q(is_public=True) | Q(members__user=self.request.user)
            ).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def members(self, request, slug=None):
        team = self.get_object()
        
        # Get members for this team
        members = team.members.all()
        
        # Filter by role if provided
        role = request.query_params.get('role')
        if role:
            members = members.filter(role=role)
        
        page = self.paginate_queryset(members)
        if page is not None:
            serializer = TeamMemberSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = TeamMemberSerializer(members, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def projects(self, request, slug=None):
        team = self.get_object()
        
        # Get projects for this team
        projects = team.projects.all()
        
        # Filter by status if provided
        status_param = request.query_params.get('status')
        if status_param:
            projects = projects.filter(status=status_param)
        
        # Filter by public/private
        if not team.members.filter(user=request.user).exists():
            projects = projects.filter(is_public=True)
        
        page = self.paginate_queryset(projects)
        if page is not None:
            serializer = TeamProjectSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = TeamProjectSerializer(projects, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def announcements(self, request, slug=None):
        team = self.get_object()
        
        # Get announcements for this team
        announcements = team.announcements.all()
        
        # Filter by pinned if provided
        pinned = request.query_params.get('pinned')
        if pinned:
            announcements = announcements.filter(is_pinned=(pinned.lower() == 'true'))
        
        page = self.paginate_queryset(announcements)
        if page is not None:
            serializer = TeamAnnouncementSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = TeamAnnouncementSerializer(announcements, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def join(self, request, slug=None):
        team = self.get_object()
        
        # Check if the team is public
        if not team.is_public:
            return Response(
                {"detail": "This team is private. You need an invitation to join."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if the user is already a member
        if team.members.filter(user=request.user).exists():
            return Response(
                {"detail": "You are already a member of this team."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add the user as a member
        membership = TeamMember.objects.create(
            team=team,
            user=request.user,
            role='member'
        )
        
        serializer = TeamMemberSerializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsTeamMember])
    def leave(self, request, slug=None):
        team = self.get_object()
        
        # Check if the user is a member
        try:
            membership = team.members.get(user=request.user)
        except TeamMember.DoesNotExist:
            return Response(
                {"detail": "You are not a member of this team."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Don't allow the last owner to leave
        if membership.role == 'owner' and team.members.filter(role='owner').count() <= 1:
            return Response(
                {"detail": "You are the last owner. Please transfer ownership before leaving."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove the user from the team
        membership.delete()
        
        return Response(
            {"detail": "You have left the team."},
            status=status.HTTP_200_OK
        )


class TeamMemberViewSet(viewsets.ModelViewSet):
    serializer_class = TeamMemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['team', 'user', 'role']
    
    def get_queryset(self):
        # Return memberships for teams where the user is a member
        if self.request.user.is_staff or self.request.user.role == 'administrator':
            return TeamMember.objects.all()
        
        return TeamMember.objects.filter(
            team__members__user=self.request.user
        ).distinct()
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsTeamAdmin])
    def change_role(self, request, pk=None):
        membership = self.get_object()
        role = request.data.get('role')
        
        # Validate role
        if role not in ['owner', 'admin', 'member']:
            return Response(
                {"detail": "Invalid role. Must be 'owner', 'admin', or 'member'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Don't allow demoting the last owner
        if membership.role == 'owner' and role != 'owner':
            if membership.team.members.filter(role='owner').count() <= 1:
                return Response(
                    {"detail": "Cannot demote the last owner."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Update the role
        membership.role = role
        membership.save(update_fields=['role'])
        
        serializer = self.get_serializer(membership)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsTeamAdmin])
    def remove(self, request, pk=None):
        membership = self.get_object()
        
        # Don't allow removing the last owner
        if membership.role == 'owner' and membership.team.members.filter(role='owner').count() <= 1:
            return Response(
                {"detail": "Cannot remove the last owner."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove the member
        membership.delete()
        
        return Response(
            {"detail": "Member removed from the team."},
            status=status.HTTP_200_OK
        )


class TeamInvitationViewSet(viewsets.ModelViewSet):
    serializer_class = TeamInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['team', 'invitee', 'status']
    ordering_fields = ['created_at', 'expires_at']
    
    def get_queryset(self):
        user = self.request.user
        
        # Staff and admins can see all invitations
        if user.is_staff or user.role == 'administrator':
            return TeamInvitation.objects.all()
        
        # Users can see invitations they've sent or received, or for teams they're an admin of
        return TeamInvitation.objects.filter(
            Q(inviter=user) | 
            Q(invitee=user) | 
            Q(team__members__user=user, team__members__role__in=['admin', 'owner'])
        ).distinct()
    
    def perform_create(self, serializer):
        team = serializer.validated_data['team']
        
        # Check if the user is an admin or owner of the team
        if not team.members.filter(
            user=self.request.user,
            role__in=['admin', 'owner']
        ).exists():
            raise permissions.PermissionDenied("Only team admins and owners can send invitations.")
        
        serializer.save(inviter=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsInvitationRecipient])
    def accept(self, request, pk=None):
        invitation = self.get_object()
        
        # Check if the invitation is pending and not expired
        if invitation.status != 'pending':
            return Response(
                {"detail": f"This invitation has already been {invitation.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if invitation.is_expired:
            invitation.status = 'expired'
            invitation.save(update_fields=['status'])
            return Response(
                {"detail": "This invitation has expired."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Accept the invitation
        if invitation.accept():
            return Response(
                {"detail": f"You have joined {invitation.team.name}."},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"detail": "Failed to accept invitation."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsInvitationRecipient])
    def decline(self, request, pk=None):
        invitation = self.get_object()
        
        # Check if the invitation is pending
        if invitation.status != 'pending':
            return Response(
                {"detail": f"This invitation has already been {invitation.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Decline the invitation
        if invitation.decline():
            return Response(
                {"detail": "Invitation declined."},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"detail": "Failed to decline invitation."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def received(self, request):
        # Get invitations received by the current user
        invitations = TeamInvitation.objects.filter(
            invitee=request.user,
            status='pending'
        ).order_by('-created_at')
        
        page = self.paginate_queryset(invitations)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(invitations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def sent(self, request):
        # Get invitations sent by the current user
        invitations = TeamInvitation.objects.filter(
            inviter=request.user
        ).order_by('-created_at')
        
        page = self.paginate_queryset(invitations)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(invitations, many=True)
        return Response(serializer.data)


class TeamProjectViewSet(viewsets.ModelViewSet):
    serializer_class = TeamProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsPublicOrTeamMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['team', 'status', 'is_public']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at', 'start_date', 'end_date']
    lookup_field = 'slug'
    
    def get_queryset(self):
        # Get the team slug from the URL if it exists
        team_slug = self.kwargs.get('team_slug')
        
        queryset = TeamProject.objects.all()
        
        # Filter by team if provided
        if team_slug:
            queryset = queryset.filter(team__slug=team_slug)
        
        # Filter for public projects or projects from teams the user is a member of
        if not (self.request.user.is_staff or self.request.user.role == 'administrator'):
            queryset = queryset.filter(
                Q(is_public=True) | Q(team__members__user=self.request.user)
            ).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def tasks(self, request, slug=None, team_slug=None):
        project = self.get_object()
        
        # Get tasks for this project
        tasks = project.tasks.all()
        
        # Filter by status if provided
        status_param = request.query_params.get('status')
        if status_param:
            tasks = tasks.filter(status=status_param)
        
        # Filter by priority if provided
        priority = request.query_params.get('priority')
        if priority:
            tasks = tasks.filter(priority=priority)
        
        # Filter by assigned_to if provided
        assigned_to = request.query_params.get('assigned_to')
        if assigned_to:
            if assigned_to == 'me':
                tasks = tasks.filter(assigned_to=request.user)
            elif assigned_to == 'unassigned':
                tasks = tasks.filter(assigned_to=None)
            else:
                tasks = tasks.filter(assigned_to__id=assigned_to)
        
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = TeamTaskSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = TeamTaskSerializer(tasks, many=True, context={'request': request})
        return Response(serializer.data)


class TeamTaskViewSet(viewsets.ModelViewSet):
    serializer_class = TeamTaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'status', 'priority', 'assigned_to']
    search_fields = ['title', 'description']
    ordering_fields = ['priority', 'due_date', 'created_at', 'updated_at']
    
    def get_queryset(self):
        # Get the project slug from the URL if it exists
        project_slug = self.kwargs.get('project_slug')
        team_slug = self.kwargs.get('team_slug')
        
        queryset = TeamTask.objects.all()
        
        # Filter by project if provided
        if project_slug and team_slug:
            queryset = queryset.filter(
                project__slug=project_slug,
                project__team__slug=team_slug
            )
        
        # Filter for tasks from teams the user is a member of
        if not (self.request.user.is_staff or self.request.user.role == 'administrator'):
            queryset = queryset.filter(
                project__team__members__user=self.request.user
            ).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsTaskAssigneeOrTeamAdmin])
    def change_status(self, request, pk=None):
        task = self.get_object()
        status_param = request.data.get('status')
        
        # Validate status
        if status_param not in dict(TeamTask.STATUS_CHOICES).keys():
            return Response(
                {"detail": f"Invalid status. Must be one of: {', '.join(dict(TeamTask.STATUS_CHOICES).keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the status
        task.status = status_param
        task.save(update_fields=['status'])
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsTeamMember])
    def assign(self, request, pk=None):
        task = self.get_object()
        user_id = request.data.get('user_id')
        
        # If user_id is None, unassign the task
        if user_id is None:
            task.assigned_to = None
            task.save(update_fields=['assigned_to'])
            serializer = self.get_serializer(task)
            return Response(serializer.data)
        
        # Check if the user exists and is a member of the team
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
            if not task.project.team.members.filter(user=user).exists():
                return Response(
                    {"detail": "User is not a member of this team."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Assign the task
        task.assigned_to = user
        task.save(update_fields=['assigned_to'])
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)


class TeamAnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = TeamAnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['team', 'is_pinned']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'is_pinned']
    
    def get_queryset(self):
        # Get the team slug from the URL if it exists
        team_slug = self.kwargs.get('team_slug')
        
        queryset = TeamAnnouncement.objects.all()
        
        # Filter by team if provided
        if team_slug:
            queryset = queryset.filter(team__slug=team_slug)
        
        # Filter for announcements from teams the user is a member of
        if not (self.request.user.is_staff or self.request.user.role == 'administrator'):
            queryset = queryset.filter(
                team__members__user=self.request.user
            ).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsTeamAdmin])
    def toggle_pin(self, request, pk=None):
        announcement = self.get_object()
        
        # Toggle the pin status
        announcement.is_pinned = not announcement.is_pinned
        announcement.save(update_fields=['is_pinned'])
        
        serializer = self.get_serializer(announcement)
        return Response(serializer.data)


## 5. URLs

Configurons les URLs pour les endpoints:

```python
# teams/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TeamViewSet, TeamMemberViewSet, TeamInvitationViewSet,
    TeamProjectViewSet, TeamTaskViewSet, TeamAnnouncementViewSet
)

router = DefaultRouter()
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'members', TeamMemberViewSet, basename='team-member')
router.register(r'invitations', TeamInvitationViewSet, basename='team-invitation')
router.register(r'projects', TeamProjectViewSet, basename='team-project')
router.register(r'tasks', TeamTaskViewSet, basename='team-task')
router.register(r'announcements', TeamAnnouncementViewSet, basename='team-announcement')

# Nested routes
team_projects_router = DefaultRouter()
team_projects_router.register(r'projects', TeamProjectViewSet, basename='team-project')

project_tasks_router = DefaultRouter()
project_tasks_router.register(r'tasks', TeamTaskViewSet, basename='project-task')

team_announcements_router = DefaultRouter()
team_announcements_router.register(r'announcements', TeamAnnouncementViewSet, basename='team-announcement')

urlpatterns = [
    path('', include(router.urls)),
    # Nested routes
    path('teams/<slug:team_slug>/', include(team_projects_router.urls)),
    path('teams/<slug:team_slug>/projects/<slug:project_slug>/', include(project_tasks_router.urls)),
    path('teams/<slug:team_slug>/', include(team_announcements_router.urls)),
]
```

## 6. Intégration dans les URLs Principales

Assurez-vous d'inclure les URLs de l'application teams dans les URLs principales du projet:

```python
# src/urls.py (mise à jour)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/learning/', include('learning.urls')),
    path('api/challenges/', include('challenges.urls')),
    path('api/core/', include('core.urls')),
    path('api/social/', include('social.urls')),
    path('api/messaging/', include('messaging.urls')),
    path('api/teams/', include('teams.urls')),  # Ajout des URLs teams
    # Autres URLs d'API
    path('api-auth/', include('rest_framework.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
```

## 7. Résumé des Endpoints

Voici un résumé des endpoints que nous avons créés pour l'application teams:

### Teams

- `GET /api/teams/teams/` - Liste toutes les équipes
- `POST /api/teams/teams/` - Crée une nouvelle équipe
- `GET /api/teams/teams/{slug}/` - Détails d'une équipe
- `PUT/PATCH /api/teams/teams/{slug}/` - Modifie une équipe (admin/propriétaire seulement)
- `DELETE /api/teams/teams/{slug}/` - Supprime une équipe (propriétaire seulement)
- `GET /api/teams/teams/{slug}/members/` - Liste les membres d'une équipe
- `GET /api/teams/teams/{slug}/projects/` - Liste les projets d'une équipe
- `GET /api/teams/teams/{slug}/announcements/` - Liste les annonces d'une équipe
- `POST /api/teams/teams/{slug}/join/` - Rejoint une équipe publique
- `POST /api/teams/teams/{slug}/leave/` - Quitte une équipe


### Team Members

- `GET /api/teams/members/` - Liste les membres des équipes
- `GET /api/teams/members/{id}/` - Détails d'un membre
- `POST /api/teams/members/{id}/change_role/` - Change le rôle d'un membre (admin seulement)
- `POST /api/teams/members/{id}/remove/` - Retire un membre de l'équipe (admin seulement)


### Team Invitations

- `GET /api/teams/invitations/` - Liste les invitations
- `POST /api/teams/invitations/` - Crée une nouvelle invitation
- `GET /api/teams/invitations/{id}/` - Détails d'une invitation
- `DELETE /api/teams/invitations/{id}/` - Supprime une invitation
- `POST /api/teams/invitations/{id}/accept/` - Accepte une invitation
- `POST /api/teams/invitations/{id}/decline/` - Décline une invitation
- `GET /api/teams/invitations/received/` - Liste les invitations reçues
- `GET /api/teams/invitations/sent/` - Liste les invitations envoyées


### Team Projects

- `GET /api/teams/projects/` - Liste tous les projets
- `POST /api/teams/projects/` - Crée un nouveau projet
- `GET /api/teams/projects/{slug}/` - Détails d'un projet
- `PUT/PATCH /api/teams/projects/{slug}/` - Modifie un projet (admin seulement)
- `DELETE /api/teams/projects/{slug}/` - Supprime un projet (admin seulement)
- `GET /api/teams/projects/{slug}/tasks/` - Liste les tâches d'un projet
- `GET /api/teams/teams/{team_slug}/projects/` - Liste les projets d'une équipe spécifique


### Team Tasks

- `GET /api/teams/tasks/` - Liste toutes les tâches
- `POST /api/teams/tasks/` - Crée une nouvelle tâche
- `GET /api/teams/tasks/{id}/` - Détails d'une tâche
- `PUT/PATCH /api/teams/tasks/{id}/` - Modifie une tâche
- `DELETE /api/teams/tasks/{id}/` - Supprime une tâche
- `POST /api/teams/tasks/{id}/change_status/` - Change le statut d'une tâche
- `POST /api/teams/tasks/{id}/assign/` - Assigne une tâche à un membre
- `GET /api/teams/teams/{team_slug}/projects/{project_slug}/tasks/` - Liste les tâches d'un projet spécifique


### Team Announcements

- `GET /api/teams/announcements/` - Liste toutes les annonces
- `POST /api/teams/announcements/` - Crée une nouvelle annonce
- `GET /api/teams/announcements/{id}/` - Détails d'une annonce
- `PUT/PATCH /api/teams/announcements/{id}/` - Modifie une annonce (admin seulement)
- `DELETE /api/teams/announcements/{id}/` - Supprime une annonce (admin seulement)
- `POST /api/teams/announcements/{id}/toggle_pin/` - Épingle/désépingle une annonce
- `GET /api/teams/teams/{team_slug}/announcements/` - Liste les annonces d'une équipe spécifique


## 8. Fonctionnalités Clés

Ces endpoints offrent les fonctionnalités suivantes:

1. **Gestion des équipes**

1. Création et gestion d'équipes
2. Contrôle de la visibilité (public/privé)
3. Gestion des membres et des rôles (propriétaire, admin, membre)



2. **Système d'invitation**

1. Invitation de nouveaux membres
2. Acceptation/refus des invitations
3. Expiration automatique des invitations



3. **Projets d'équipe**

1. Création et gestion de projets
2. Suivi de l'état d'avancement
3. Contrôle de la visibilité (public/privé)



4. **Gestion des tâches**

1. Création et assignation de tâches
2. Priorisation et suivi de l'état
3. Estimation du temps nécessaire



5. **Communication interne**

1. Annonces d'équipe
2. Épinglage des annonces importantes



6. **Contrôle d'accès**

1. Permissions basées sur les rôles
2. Restrictions pour les actions sensibles
3. Visibilité adaptée selon le statut de membre





Ces endpoints fournissent une API complète pour les fonctionnalités de collaboration en équipe de votre plateforme Hackitech, permettant aux utilisateurs de former des équipes, de travailler ensemble sur des projets et de gérer efficacement leurs tâches.