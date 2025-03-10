# learning/serializers.py
from rest_framework import serializers

from core.serializers import TagSerializer

from .models import (Answer, Course, LearningPath, Module, Question, Quiz,
                     UserCourseProgress, UserModuleProgress, UserQuizAttempt)


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'answer_text', 'is_correct', 'order']
        extra_kwargs = {
            'is_correct': {'write_only': True}  # Hide correct answer from users
        }


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'question_type', 'code_snippet', 
                  'explanation', 'order', 'points', 'answers']


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'module', 'order', 
                  'passing_score', 'time_limit_minutes', 'is_published', 
                  'created_at', 'updated_at', 'questions', 'question_count']
    
    def get_question_count(self, obj):
        return obj.questions.count()


class ModuleSerializer(serializers.ModelSerializer):
    quizzes = QuizSerializer(many=True, read_only=True)
    
    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'course', 'order', 
                  'content', 'estimated_minutes', 'is_published', 
                  'created_at', 'updated_at', 'quizzes']


class CourseSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    completion_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'slug', 'image', 
                  'learning_path', 'order_in_path', 'difficulty', 
                  'estimated_hours', 'is_published', 'is_featured', 
                  'requires_subscription', 'created_by', 'created_at', 
                  'updated_at', 'tags', 'modules', 'completion_percentage']
    
    def get_completion_percentage(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_completion_percentage(request.user)
        return 0


class LearningPathSerializer(serializers.ModelSerializer):
    courses = CourseSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    completion_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningPath
        fields = ['id', 'title', 'description', 'slug', 'image', 
                  'difficulty', 'estimated_hours', 'is_published', 
                  'is_featured', 'created_by', 'created_at', 
                  'updated_at', 'tags', 'courses', 'completion_percentage']
    
    def get_completion_percentage(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_completion_percentage(request.user)
        return 0


class UserCourseProgressSerializer(serializers.ModelSerializer):
    course_details = CourseSerializer(source='course', read_only=True)
    
    class Meta:
        model = UserCourseProgress
        fields = ['id', 'user', 'course', 'course_details', 'started_at', 
                  'last_activity', 'is_completed', 'completed_at']
        read_only_fields = ['id', 'user', 'started_at', 'last_activity', 'completed_at']


class UserModuleProgressSerializer(serializers.ModelSerializer):
    module_details = ModuleSerializer(source='module', read_only=True)
    
    class Meta:
        model = UserModuleProgress
        fields = ['id', 'user', 'module', 'module_details', 'started_at', 
                  'last_activity', 'is_completed', 'completed_at']
        read_only_fields = ['id', 'user', 'started_at', 'last_activity', 'completed_at']


class UserQuizAttemptSerializer(serializers.ModelSerializer):
    quiz_details = QuizSerializer(source='quiz', read_only=True)
    
    class Meta:
        model = UserQuizAttempt
        fields = ['id', 'user', 'quiz', 'quiz_details', 'score', 'passed', 
                  'started_at', 'completed_at', 'time_spent_seconds']
        read_only_fields = ['id', 'user', 'started_at']


# Serializers for creating and updating
class QuestionCreateUpdateSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)
    
    class Meta:
        model = Question
        fields = ['id', 'quiz', 'question_text', 'question_type', 'code_snippet', 
                  'explanation', 'order', 'points', 'answers']
    
    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        question = Question.objects.create(**validated_data)
        
        for answer_data in answers_data:
            Answer.objects.create(question=question, **answer_data)
        
        return question
    
    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', None)
        
        # Update Question fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update or create answers
        if answers_data is not None:
            # Delete existing answers not in the update
            answer_ids = [a.get('id') for a in answers_data if a.get('id')]
            instance.answers.exclude(id__in=answer_ids).delete()
            
            # Update or create answers
            for answer_data in answers_data:
                answer_id = answer_data.get('id')
                if answer_id:
                    answer = Answer.objects.get(id=answer_id)
                    for attr, value in answer_data.items():
                        if attr != 'id':
                            setattr(answer, attr, value)
                    answer.save()
                else:
                    Answer.objects.create(question=instance, **answer_data)
        
        return instance


class QuizSubmissionSerializer(serializers.Serializer):
    answers = serializers.DictField(
        child=serializers.UUIDField(),
        help_text="Dictionary mapping question IDs to answer IDs"
    )
    time_spent_seconds = serializers.IntegerField(min_value=0)