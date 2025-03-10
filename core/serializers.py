# core/serializers.py
from rest_framework import serializers

from .models import Audit, Category, Feedback, Setting, Skill, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'description', 'color']
        read_only_fields = ['id']


class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent', 'parent_name', 
                  'icon', 'color', 'children']
        read_only_fields = ['id', 'children']
    
    def get_children(self, obj):
        children = Category.objects.filter(parent=obj)
        if not children:
            return []
        return CategorySerializer(children, many=True, context=self.context).data


class SkillSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    related_skills_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Skill
        fields = ['id', 'name', 'slug', 'description', 'skill_type', 'icon', 
                  'parent', 'parent_name', 'related_skills', 'related_skills_details']
        read_only_fields = ['id', 'related_skills_details']
    
    def get_related_skills_details(self, obj):
        related = obj.related_skills.all()
        if not related:
            return []
        return SkillMinimalSerializer(related, many=True, context=self.context).data


class SkillMinimalSerializer(serializers.ModelSerializer):
    """A minimal serializer for Skill to avoid recursion in related_skills."""
    class Meta:
        model = Skill
        fields = ['id', 'name', 'slug', 'skill_type', 'icon']


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = ['key', 'value', 'description', 'is_public', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class FeedbackSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Feedback
        fields = ['id', 'user', 'username', 'feedback_type', 'title', 'description', 
                  'screenshot', 'status', 'created_at', 'updated_at', 'resolved_at']
        read_only_fields = ['id', 'user', 'username', 'created_at', 'updated_at', 'resolved_at']
    
    def create(self, validated_data):
        # Add the user from the request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AuditSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Audit
        fields = ['id', 'user', 'username', 'action', 'entity_type', 'entity_id', 
                  'description', 'ip_address', 'user_agent', 'timestamp']
        read_only_fields = ['id', 'user', 'username', 'ip_address', 'user_agent', 'timestamp']