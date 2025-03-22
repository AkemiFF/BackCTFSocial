# accounts/serializers.py
from django.contrib.auth.validators import UnicodeUsernameValidator
from rest_framework import serializers

from accounts.models import Skill

from .models import *


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'skill_type']
        extra_kwargs = {
            'name': {'required': False}
        }

class UserProfileSerializer(serializers.ModelSerializer):
    skills = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Skill.objects.all(),
        required=False,
        allow_empty=True
    )

    class Meta:
        model = UserProfile
        fields = [
            'display_name', 'location', 'skills', 'interests', 
            'experience_level', 'job_title', 'company', 
            'show_email', 'show_points'
        ]

    def update(self, instance, validated_data):
        skills_data = validated_data.pop('skills', None)
        instance = super().update(instance, validated_data)
        if skills_data is not None:
            instance.skills.set(skills_data)
        return instance
    

class UserProfileDetailsSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(
        many=True,
        required=False,
        allow_empty=True
    )

    class Meta:
        model = UserProfile
        fields = [
            'display_name', 'location', 'skills', 'interests', 
            'experience_level', 'job_title', 'company', 
            'show_email', 'show_points'
        ]

    
class UserProjectsSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = UserProjects
        fields = [
            'id', 'user', 'project_name', 'description', 'link', 'language', 
            'image', 'created_at', 'updated_at'
        ]
        extra_kwargs = {       
          'image': {'required': False, 'allow_null': True}
        }
        
class UserDetailsSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)
    user_projects = UserProjectsSerializer(
        many=True, 
        required=True, 
    )
    location = serializers.CharField(source='profile.location', required=False)
    website = serializers.CharField(source='website_url', required=False)
    github = serializers.CharField(source='github_url', required=False)
    gitlab = serializers.CharField(source='gitlab_url', required=False)
    avatar = serializers.ImageField(source='photo', required=False)
    coverImage = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'name', 'email', 'bio', 'avatar', 'coverImage',
            'location', 'website', 'github', 'gitlab', 'twitter_url', 'linkedin_url',
            'profile', 'user_projects'
        ]
        extra_kwargs = {
            'name': {'required': False}
        }

    def update(self, instance, validated_data):
        print("\nValidated data : ",validated_data)
        # Extraire les données imbriquées manuellement
        profile_data = validated_data.pop('profile', {})
        projects_data = validated_data.pop('user_projects', [])

        # Mise à jour de l'utilisateur
        instance = super().update(instance, validated_data)

        # Mise à jour du profil (avec gestion des compétences)
        if profile_data:
            profile = instance.profile
            skills_data = profile_data.pop('skills', None)
            profile_serializer = UserProfileSerializer(profile, data=profile_data, partial=True)
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()
            if skills_data is not None:
                profile.skills.set(skills_data)

        # Mise à jour des projets
        for project_data in projects_data:
            project_id = project_data.get('id')
            if project_id:
                project = UserProjects.objects.get(id=project_id, user=instance)
                project_serializer = UserProjectsSerializer(project, data=project_data, partial=True)
            else:
                project_serializer = UserProjectsSerializer(data=project_data)
            project_serializer.is_valid(raise_exception=True)
            project_serializer.save(user=instance)

        return instance
    
  
class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileDetailsSerializer(required=False)
    user_projects = UserProjectsSerializer( many=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'email', 'name','username', 'first_name', 'last_name', 'bio', 
                  'photo', 'points', 'role', 'is_verified', 'date_joined', 
                  'last_active', 'github_url', 'linkedin_url', 'twitter_url', 
                  'website_url', 'profile','user_projects']
        read_only_fields = ['id', 'points', 'is_verified', 'date_joined', 'last_active']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        user = User.objects.create_user(**validated_data)
        
        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)
        else:
            UserProfile.objects.create(user=user)
            
        return user
    


class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = ['id', 'session_key', 'ip_address', 'user_agent', 'device_type', 
                  'location', 'started_at', 'last_activity', 'is_active']
        read_only_fields = ['id', 'user', 'started_at', 'last_activity']


class UserFollowingSerializer(serializers.ModelSerializer):
    following_user_details = UserSerializer(source='following_user', read_only=True)
    
    class Meta:
        model = UserFollowing
        fields = ['id', 'following_user', 'following_user_details', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
        
class InitiateRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()

class CompleteRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    username = serializers.CharField(
        max_length=150,
        validators=[UnicodeUsernameValidator()]
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )