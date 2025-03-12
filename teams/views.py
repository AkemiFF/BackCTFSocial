# teams/views.py
from django.db.models import Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (Team, TeamAnnouncement, TeamInvitation, TeamMember,
                     TeamProject, TeamTask)
from .permissions import (IsInvitationRecipient, IsPublicOrTeamMember,
                          IsTaskAssigneeOrTeamAdmin, IsTeamAdmin, IsTeamMember,
                          IsTeamOwner)
from .serializers import (TeamAnnouncementSerializer, TeamInvitationSerializer,
                          TeamMemberSerializer, TeamProjectSerializer,
                          TeamSerializer, TeamTaskSerializer)


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
