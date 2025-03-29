# serializers.py
from rest_framework import serializers

from .models import Challenge, ChallengeType


class ChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = '__all__'
        
class ChallengeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeType
        fields = '__all__'

from rest_framework import serializers

from .models import (Challenge, ChallengeCategory, ChallengeType,
                     DockerConfigTemplate)


class ChallengeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeType
        fields = ['id', 'name', 'slug', 'validation_type', 'icon']

class DockerConfigTemplateSerializer(serializers.ModelSerializer):
    challenge_type = ChallengeTypeSerializer(read_only=True)
    challenge_type_id = serializers.PrimaryKeyRelatedField(
        queryset=ChallengeType.objects.all(),
        source='challenge_type',
        write_only=True
    )
    
    class Meta:
        model = DockerConfigTemplate
        fields = ['id', 'challenge_type', 'challenge_type_id', 'dockerfile', 'default_ports', 'common_commands']

class ChallengeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeCategory
        fields = ['id', 'name', 'description']

class ChallengeSerializer(serializers.ModelSerializer):
    challenge_type = ChallengeTypeSerializer(read_only=True)
    challenge_type_id = serializers.PrimaryKeyRelatedField(
        queryset=ChallengeType.objects.all(),
        source='challenge_type',
        write_only=True
    )
    categories = ChallengeCategorySerializer(many=True, read_only=True, source='challengecategory_set')
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=ChallengeCategory.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Challenge
        fields = [
            'id', 'title', 'challenge_type', 'challenge_type_id', 'difficulty', 
            'description', 'points', 'docker_image', 'docker_ports', 
            'environment_vars', 'startup_command', 'static_flag', 
            'flag_generation_script', 'validation_script', 'created_at', 
            'is_active', 'dockerfile', 'docker_context', 'built_image', 
            'setup_ssh', 'categories', 'category_ids'
        ]
        read_only_fields = ['id', 'created_at', 'built_image']
    
    def create(self, validated_data):
        category_ids = validated_data.pop('category_ids', [])
        challenge = Challenge.objects.create(**validated_data)
        
        if category_ids:
            for category in category_ids:
                challenge.challengecategory_set.add(category)
        
        return challenge
    
    def update(self, instance, validated_data):
        category_ids = validated_data.pop('category_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        if category_ids is not None:
            instance.challengecategory_set.clear()
            for category in category_ids:
                instance.challengecategory_set.add(category)
        
        return instance

