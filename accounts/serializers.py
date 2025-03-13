# accounts/serializers.py
from django.contrib.auth.validators import UnicodeUsernameValidator
from rest_framework import serializers

from .models import User, UserFollowing, UserProfile, UserSession


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['display_name', 'location', 'experience_level', 'job_title', 
                  'company', 'show_email', 'show_points']
        read_only_fields = ['user']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'bio', 
                  'photo', 'points', 'role', 'is_verified', 'date_joined', 
                  'last_active', 'github_url', 'linkedin_url', 'twitter_url', 
                  'website_url', 'profile']
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
    
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        
        # Update User fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update Profile fields
        if profile_data and hasattr(instance, 'profile'):
            for attr, value in profile_data.items():
                setattr(instance.profile, attr, value)
            instance.profile.save()
            
        return instance


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