# social/serializers.py
from rest_framework import serializers

from accounts.serializers import UserSerializer
from core.serializers import SkillSerializer, TagSerializer

from .models import (Comment, Conversation, Message, Post, Project,
                     SocialInteraction)


class CommentSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    reply_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'post', 'user', 'user_details', 'content', 'parent',
                  'created_at', 'updated_at', 'is_edited', 'reply_count',
                  'like_count', 'is_liked']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'is_edited']
    
    def get_reply_count(self, obj):
        return obj.replies.count()
    
    def get_like_count(self, obj):
        return obj.interactions.filter(interaction_type='like').count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return SocialInteraction.objects.filter(
            user=request.user,
            comment=obj,
            interaction_type='like'
        ).exists()
    
    def create(self, validated_data):
        # Add the user from the request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PostSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    share_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['id', 'user', 'user_details', 'content', 'post_type',
                  'image', 'code_snippet', 'code_language', 'link_url',
                  'link_title', 'link_description', 'link_image',
                  'created_at', 'updated_at', 'is_edited', 'is_pinned',
                  'is_public', 'tags', 'comment_count', 'like_count',
                  'share_count', 'is_liked', 'is_saved']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'is_edited']
    
    def get_comment_count(self, obj):
        return obj.comments.count()
    
    def get_like_count(self, obj):
        return obj.interactions.filter(interaction_type='like').count()
    
    def get_share_count(self, obj):
        return obj.interactions.filter(interaction_type='share').count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return SocialInteraction.objects.filter(
            user=request.user,
            post=obj,
            interaction_type='like'
        ).exists()
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return SocialInteraction.objects.filter(
            user=request.user,
            post=obj,
            interaction_type='save'
        ).exists()
    
    def create(self, validated_data):
        # Add the user from the request
        validated_data['user'] = self.context['request'].user
        
        # Handle tags
        tags_data = self.context['request'].data.get('tags', [])
        
        post = Post.objects.create(**validated_data)
        
        # Add tags
        if tags_data:
            post.tags.set(tags_data)
        
        return post
    
    def update(self, instance, validated_data):
        # Update Post fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Mark as edited if content changed
        if 'content' in validated_data:
            instance.is_edited = True
        
        instance.save()
        
        # Handle tags
        tags_data = self.context['request'].data.get('tags', None)
        if tags_data is not None:
            instance.tags.set(tags_data)
        
        return instance


class SocialInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialInteraction
        fields = ['id', 'user', 'post', 'comment', 'interaction_type', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
    
    def validate(self, data):
        # Ensure either post or comment is provided, but not both
        if data.get('post') and data.get('comment'):
            raise serializers.ValidationError("Cannot specify both post and comment.")
        if not data.get('post') and not data.get('comment'):
            raise serializers.ValidationError("Must specify either post or comment.")
        
        # Validate interaction type for comments
        if data.get('comment') and data.get('interaction_type') not in ['like', 'report']:
            raise serializers.ValidationError("Only 'like' and 'report' interactions are allowed for comments.")
        
        return data
    
    def create(self, validated_data):
        # Add the user from the request
        validated_data['user'] = self.context['request'].user
        
        # Check if the interaction already exists
        filters = {
            'user': validated_data['user'],
            'interaction_type': validated_data['interaction_type']
        }
        
        if validated_data.get('post'):
            filters['post'] = validated_data['post']
        elif validated_data.get('comment'):
            filters['comment'] = validated_data['comment']
        
        try:
            # If it exists, return the existing interaction
            return SocialInteraction.objects.get(**filters)
        except SocialInteraction.DoesNotExist:
            # Otherwise create a new one
            return super().create(validated_data)


class MessageSerializer(serializers.ModelSerializer):
    sender_details = UserSerializer(source='sender', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_details', 'message_type',
                  'content', 'image', 'file', 'code_snippet', 'code_language',
                  'created_at', 'is_read', 'read_by']
        read_only_fields = ['id', 'sender', 'created_at', 'is_read', 'read_by']
    
    def create(self, validated_data):
        # Add the sender from the request
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


class ConversationSerializer(serializers.ModelSerializer):
    participants_details = UserSerializer(source='participants', many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'participants_details', 'created_at',
                  'updated_at', 'is_group', 'name', 'last_message', 'unread_count']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if not last_msg:
            return None
        return {
            'id': last_msg.id,
            'content': last_msg.content,
            'sender': last_msg.sender.username,
            'created_at': last_msg.created_at,
            'is_read': last_msg.is_read
        }
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        
        return obj.messages.exclude(sender=request.user).exclude(read_by=request.user).count()
    
    def create(self, validated_data):
        participants_data = validated_data.pop('participants')
        
        # Ensure the current user is included in participants
        user = self.context['request'].user
        if user.id not in [user.id for user in participants_data]:
            participants_data.append(user)
        
        # Create the conversation
        conversation = Conversation.objects.create(**validated_data)
        
        # Add participants
        conversation.participants.set(participants_data)
        
        return conversation


class ProjectSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    technologies_details = SkillSerializer(source='technologies', many=True, read_only=True)
    
    class Meta:
        model = Project
        fields = ['id', 'user', 'user_details', 'title', 'description', 'image',
                  'repository_url', 'demo_url', 'technologies', 'technologies_details',
                  'created_at', 'updated_at', 'is_public']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Add the user from the request
        validated_data['user'] = self.context['request'].user
        
        # Handle technologies
        technologies_data = self.context['request'].data.get('technologies', [])
        
        project = Project.objects.create(**validated_data)
        
        # Add technologies
        if technologies_data:
            project.technologies.set(technologies_data)
        
        return project
    
    def update(self, instance, validated_data):
        # Update Project fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Handle technologies
        technologies_data = self.context['request'].data.get('technologies', None)
        if technologies_data is not None:
            instance.technologies.set(technologies_data)
        
        return instance