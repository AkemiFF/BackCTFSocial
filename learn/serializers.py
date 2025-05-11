from ctf.models import *
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class CourseTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseTag
        fields = ['id', 'name']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class CourseListSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField() 
    progress = serializers.SerializerMethodField()
    nb_modules = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'level', 'category',
            'duration', 'instructor', 'image', 'students', 'rating',
            'tags', 'progress','nb_modules'
        ]
    
    def get_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                progress = UserProgress.objects.get(user=request.user, course=obj)
                return progress.progress
            except UserProgress.DoesNotExist:
                return 0
        return 0
    
    def get_nb_modules(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.modules.count()
        return 0
    
    def get_tags(self, obj):
        # Récupérer les tags via la relation CourseTag
        tags = obj.course_tags.all().select_related('tag')
        return TagSerializer(
            [course_tag.tag for course_tag in tags],
            many=True,
            context=self.context
        ).data
    
class ModuleListSerializer(serializers.ModelSerializer):
    completed = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = ['id', 'title', 'duration', 'order', 'points', 'completed']
    
    def get_completed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ModuleCompletion.objects.filter(
                user=request.user, module=obj
            ).exists()
        return False

class CourseDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(source='course_tags.tag', many=True, read_only=True)
    modules = ModuleListSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()
    certification = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'level', 'category',
            'duration', 'prerequisites', 'instructor', 'image', 'students',
            'rating', 'tags', 'modules', 'progress', 'certification'
        ]
    
    def get_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                progress = UserProgress.objects.get(user=request.user, course=obj)
                return progress.progress
            except UserProgress.DoesNotExist:
                return 0
        return 0
    
    def get_certification(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                cert = Certification.objects.get(user=request.user, course=obj)
                return {
                    'id': cert.id,
                    'certificate_id': cert.certificate_id,
                    'issued_at': cert.issued_at
                }
            except Certification.DoesNotExist:
                return None
        return None

class TextContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextContent
        fields = ['content']

class ImageContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageContent
        fields = ['image', 'position']

class VideoContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoContent
        fields = ['url', 'platform', 'video_file']

class FileContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileContent
        fields = ['file', 'filename', 'description', 'file_size']

class LinkContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkContent
        fields = ['url', 'description']

class ContentItemSerializer(serializers.ModelSerializer):
    text_content = TextContentSerializer(read_only=True)
    image_content = ImageContentSerializer(read_only=True)
    video_content = VideoContentSerializer(read_only=True)
    file_content = FileContentSerializer(read_only=True)
    link_content = LinkContentSerializer(read_only=True)
    
    class Meta:
        model = ContentItem
        fields = [
            'id', 'type', 'order', 'text_content', 'image_content',
            'video_content', 'file_content', 'link_content'
        ]

class QuizOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizOption
        fields = ['id', 'text',"is_correct"]

class QuizQuestionSerializer(serializers.ModelSerializer):
    options = QuizOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuizQuestion
        fields = ['id', 'question', 'type', 'order', 'options']

class ModuleDetailSerializer(serializers.ModelSerializer):
    content_items = ContentItemSerializer(many=True, read_only=True)
    quiz_questions = QuizQuestionSerializer(many=True, read_only=True)
    completed = serializers.SerializerMethodField()
    course = CourseListSerializer(read_only=True)
    
    class Meta:
        model = Module
        fields = [
            'id', 'title', 'duration', 'order', 'points',
            'content_items', 'quiz_questions', 'completed', 'course'
        ]
    
    def get_completed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ModuleCompletion.objects.filter(
                user=request.user, module=obj
            ).exists()
        return False

class QuizAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    answer = serializers.JSONField()  # Peut être un ID d'option ou une réponse textuelle

class QuizSubmissionSerializer(serializers.Serializer):
    answers = QuizAnswerSerializer(many=True)
    time_spent = serializers.IntegerField()

class QuizFeedbackSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    correct = serializers.BooleanField()
    feedback = serializers.CharField()

class QuizResultSerializer(serializers.Serializer):
    score = serializers.IntegerField()
    total = serializers.IntegerField()
    passed = serializers.BooleanField()
    feedback = QuizFeedbackSerializer(many=True)

class UserProgressSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    
    class Meta:
        model = UserProgress
        fields = ['course', 'progress', 'last_activity']

class CertificationSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    
    class Meta:
        model = Certification
        fields = ['id', 'course', 'certificate_id', 'issued_at']

class PointsTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointsTransaction
        fields = ['id', 'points', 'transaction_type', 'description', 'created_at']

class UserPointsSerializer(serializers.Serializer):
    points = serializers.IntegerField()
    level = serializers.IntegerField()
    next_level_points = serializers.IntegerField()
    level_progress = serializers.FloatField()
   
