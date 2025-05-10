# serializers.py
from rest_framework import serializers

from .models import *


class ChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = '__all__'
        
class ChallengeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeType        
        fields = '__all__'
        
class DockerConfigTemplateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DockerConfigTemplate
        fields = '__all__'

class FlagSubmissionSerializer(serializers.Serializer):
    challenge_id = serializers.PrimaryKeyRelatedField(
        queryset=Challenge.objects.all(),
        required=True
    )
    submitted_flag = serializers.CharField(
        max_length=255, 
        required=True, 
        trim_whitespace=True
    )

class ChallengeSubmissionSerializer(serializers.ModelSerializer):
    challenge_id = serializers.PrimaryKeyRelatedField(
        source='challenge',
        queryset=Challenge.objects.all(),
        required=True
    )

    class Meta:
        model = ChallengeSubmission
        fields = ['challenge_id', 'submitted_flag']
        extra_kwargs = {
            'submitted_flag': {'trim_whitespace': False}
        }
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
    is_solved = serializers.SerializerMethodField()
    class Meta:
        model = Challenge
        fields = [
            'id', 'title', 'challenge_type', 'challenge_type_id', 'difficulty', 
            'description', 'points', 'docker_image', 'docker_ports', 
            'environment_vars', 'startup_command', 'static_flag', 
            'flag_generation_script', 'validation_script', 'created_at', 
            'is_active', 'dockerfile', 'docker_context', 'built_image', 
            'setup_ssh', 'categories', 'category_ids','is_solved'
        ]
        read_only_fields = ['id', 'created_at', 'built_image']
    
    def get_is_solved(self, obj):
        """Détermine si l'utilisateur actuel a terminé le défi avec succès."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ChallengeSubmission.objects.filter(
                user=request.user,
                challenge=obj,
                is_correct=True
            ).exists()
        return False
    
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

