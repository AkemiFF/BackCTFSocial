# teams/serializers.py
from django.utils import timezone
from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import (Team, TeamAnnouncement, TeamInvitation, TeamMember,
                     TeamProject, TeamTask)


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