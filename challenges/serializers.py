# challenges/serializers.py
from rest_framework import serializers

from core.serializers import CategorySerializer, TagSerializer

from .models import (Challenge, ChallengeCompletion, ChallengeRating, Hint,
                     Resource, Submission, UserHint)


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ['id', 'name', 'resource_type', 'file', 'url', 
                  'docker_image', 'description']


class HintSerializer(serializers.ModelSerializer):
    is_unlocked = serializers.SerializerMethodField()
    
    class Meta:
        model = Hint
        fields = ['id', 'order', 'cost', 'is_unlocked']
        # Content is only shown if unlocked
    
    def get_is_unlocked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return UserHint.objects.filter(
            user=request.user,
            hint=obj
        ).exists()


class HintDetailSerializer(serializers.ModelSerializer):
    is_unlocked = serializers.SerializerMethodField()
    
    class Meta:
        model = Hint
        fields = ['id', 'content', 'order', 'cost', 'is_unlocked']
    
    def get_is_unlocked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return UserHint.objects.filter(
            user=request.user,
            hint=obj
        ).exists()


class ChallengeSerializer(serializers.ModelSerializer):
    category_details = CategorySerializer(source='category', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    resources = ResourceSerializer(many=True, read_only=True)
    hints = HintSerializer(many=True, read_only=True)
    is_completed = serializers.SerializerMethodField()
    completion_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Challenge
        fields = ['id', 'title', 'description', 'difficulty', 'points', 
                  'category', 'category_details', 'tags', 'created_by', 
                  'created_at', 'updated_at', 'status', 'is_featured', 
                  'requires_subscription', 'max_attempts', 'time_limit_minutes',
                  'resources', 'hints', 'is_completed', 'completion_count',
                  'average_rating']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
        extra_kwargs = {
            'flag': {'write_only': True}  # Never expose the flag
        }
    
    def get_is_completed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return ChallengeCompletion.objects.filter(
            user=request.user,
            challenge=obj
        ).exists()
    
    def get_completion_count(self, obj):
        return obj.completions.count()
    
    def get_average_rating(self, obj):
        ratings = obj.ratings.all()
        if not ratings:
            return None
        return sum(r.rating for r in ratings) / ratings.count()


class ChallengeDetailSerializer(ChallengeSerializer):
    user_attempts = serializers.SerializerMethodField()
    user_hints = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    
    class Meta(ChallengeSerializer.Meta):
        fields = ChallengeSerializer.Meta.fields + ['user_attempts', 'user_hints', 'user_rating']
    
    def get_user_attempts(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        
        return Submission.objects.filter(
            user=request.user,
            challenge=obj
        ).count()
    
    def get_user_hints(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return []
        
        user_hints = UserHint.objects.filter(
            user=request.user,
            challenge=obj
        ).values_list('hint_id', flat=True)
        
        return list(user_hints)
    
    def get_user_rating(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            rating = ChallengeRating.objects.get(
                user=request.user,
                challenge=obj
            )
            return rating.rating
        except ChallengeRating.DoesNotExist:
            return None


class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['id', 'challenge', 'submitted_flag', 'is_correct', 
                  'submission_time', 'points_awarded', 'attempt_number', 
                  'time_spent_seconds']
        read_only_fields = ['id', 'is_correct', 'submission_time', 
                           'points_awarded', 'attempt_number']
    
    def create(self, validated_data):
        # Add the user from the request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserHintSerializer(serializers.ModelSerializer):
    hint_content = serializers.CharField(source='hint.content', read_only=True)
    
    class Meta:
        model = UserHint
        fields = ['id', 'challenge', 'hint', 'hint_content', 'unlocked_at', 'points_deducted']
        read_only_fields = ['id', 'unlocked_at', 'points_deducted', 'hint_content']
    
    def create(self, validated_data):
        # Add the user from the request
        validated_data['user'] = self.context['request'].user
        
        # Check if the hint is already unlocked
        existing = UserHint.objects.filter(
            user=validated_data['user'],
            hint=validated_data['hint']
        ).first()
        
        if existing:
            return existing
        
        # Calculate points to deduct
        hint = validated_data['hint']
        points_deducted = hint.cost
        
        # Deduct points from user
        user = validated_data['user']
        if user.points < points_deducted:
            raise serializers.ValidationError(
                "You don't have enough points to unlock this hint."
            )
        
        user.points -= points_deducted
        user.save(update_fields=['points'])
        
        # Add points_deducted to validated_data
        validated_data['points_deducted'] = points_deducted
        
        return super().create(validated_data)


class ChallengeRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeRating
        fields = ['id', 'challenge', 'rating', 'feedback', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        # Add the user from the request
        validated_data['user'] = self.context['request'].user
        
        # Check if the user has already rated this challenge
        existing = ChallengeRating.objects.filter(
            user=validated_data['user'],
            challenge=validated_data['challenge']
        ).first()
        
        if existing:
            # Update the existing rating
            for attr, value in validated_data.items():
                setattr(existing, attr, value)
            existing.save()
            return existing
        
        return super().create(validated_data)


class ChallengeCompletionSerializer(serializers.ModelSerializer):
    challenge_details = ChallengeSerializer(source='challenge', read_only=True)
    
    class Meta:
        model = ChallengeCompletion
        fields = ['id', 'challenge', 'challenge_details', 'completed_at', 
                  'points_earned', 'time_spent_seconds', 'attempts']
        read_only_fields = ['id', 'user', 'completed_at', 'points_earned', 
                           'time_spent_seconds', 'attempts']


class FlagSubmissionSerializer(serializers.Serializer):
    flag = serializers.CharField(max_length=255)
    time_spent_seconds = serializers.IntegerField(min_value=0)