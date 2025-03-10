# learning/views.py
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (Answer, Course, LearningPath, Module, Question, Quiz,
                     UserCourseProgress, UserModuleProgress, UserQuizAttempt)
from .permissions import IsInstructorOrReadOnly, IsOwnerOrInstructor
from .serializers import (CourseSerializer, LearningPathSerializer,
                          ModuleSerializer, QuestionCreateUpdateSerializer,
                          QuestionSerializer, QuizSerializer,
                          QuizSubmissionSerializer,
                          UserCourseProgressSerializer,
                          UserModuleProgressSerializer,
                          UserQuizAttemptSerializer)


class LearningPathViewSet(viewsets.ModelViewSet):
    queryset = LearningPath.objects.all()
    serializer_class = LearningPathSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['difficulty', 'is_published', 'is_featured']
    search_fields = ['title', 'description', 'tags__name']
    ordering_fields = ['title', 'created_at', 'estimated_hours']
    lookup_field = 'slug'
    
    def get_queryset(self):
        queryset = LearningPath.objects.all()
        
        # Non-instructors can only see published paths
        if not (self.request.user.role in ['mentor', 'administrator'] or self.request.user.is_staff):
            queryset = queryset.filter(is_published=True)
        
        # Filter by tag if provided
        tag = self.request.query_params.get('tag', None)
        if tag:
            queryset = queryset.filter(tags__name=tag)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def enroll(self, request, slug=None):
        learning_path = self.get_object()
        
        # Enroll in all courses in the learning path
        for course in learning_path.courses.all():
            UserCourseProgress.objects.get_or_create(
                user=request.user,
                course=course
            )
        
        return Response(
            {"detail": f"Successfully enrolled in {learning_path.title}."}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def enrolled(self, request):
        # Get learning paths where the user is enrolled in at least one course
        enrolled_courses = UserCourseProgress.objects.filter(user=request.user).values_list('course', flat=True)
        learning_paths = LearningPath.objects.filter(courses__in=enrolled_courses).distinct()
        
        page = self.paginate_queryset(learning_paths)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(learning_paths, many=True)
        return Response(serializer.data)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['difficulty', 'is_published', 'is_featured', 'requires_subscription', 'learning_path']
    search_fields = ['title', 'description', 'tags__name']
    ordering_fields = ['title', 'created_at', 'estimated_hours']
    lookup_field = 'slug'
    
    def get_queryset(self):
        queryset = Course.objects.all()
        
        # Non-instructors can only see published courses
        if not (self.request.user.role in ['mentor', 'administrator'] or self.request.user.is_staff):
            queryset = queryset.filter(is_published=True)
            
            # Filter out subscription-required courses if user doesn't have a subscription
            # This is a placeholder - you'll need to implement subscription logic
            if not getattr(self.request.user, 'has_subscription', False):
                queryset = queryset.filter(requires_subscription=False)
        
        # Filter by tag if provided
        tag = self.request.query_params.get('tag', None)
        if tag:
            queryset = queryset.filter(tags__name=tag)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def enroll(self, request, slug=None):
        course = self.get_object()
        
        # Check if the course requires a subscription
        if course.requires_subscription and not getattr(request.user, 'has_subscription', False):
            return Response(
                {"detail": "This course requires a subscription."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Enroll in the course
        progress, created = UserCourseProgress.objects.get_or_create(
            user=request.user,
            course=course
        )
        
        if created:
            return Response(
                {"detail": f"Successfully enrolled in {course.title}."}, 
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"detail": f"You are already enrolled in {course.title}."}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def enrolled(self, request):
        enrolled_courses = Course.objects.filter(
            user_progress__user=request.user
        ).distinct()
        
        page = self.paginate_queryset(enrolled_courses)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(enrolled_courses, many=True)
        return Response(serializer.data)


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['course', 'is_published']
    ordering_fields = ['order', 'created_at']
    
    def get_queryset(self):
        queryset = Module.objects.all()
        
        # Non-instructors can only see published modules
        if not (self.request.user.role in ['mentor', 'administrator'] or self.request.user.is_staff):
            queryset = queryset.filter(is_published=True)
            
            # Filter out modules from subscription-required courses if user doesn't have a subscription
            if not getattr(self.request.user, 'has_subscription', False):
                queryset = queryset.filter(course__requires_subscription=False)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        module = self.get_object()
        
        # Check if the user is enrolled in the course
        try:
            UserCourseProgress.objects.get(user=request.user, course=module.course)
        except UserCourseProgress.DoesNotExist:
            return Response(
                {"detail": "You must be enrolled in the course to mark a module as completed."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark the module as completed
        progress, created = UserModuleProgress.objects.get_or_create(
            user=request.user,
            module=module
        )
        
        if not progress.is_completed:
            progress.mark_completed()
            return Response(
                {"detail": f"Module '{module.title}' marked as completed."}, 
                status=status.HTTP_200_OK
            )
        return Response(
            {"detail": f"Module '{module.title}' was already marked as completed."}, 
            status=status.HTTP_200_OK
        )


class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['module', 'is_published']
    ordering_fields = ['order', 'created_at']
    
    def get_queryset(self):
        queryset = Quiz.objects.all()
        
        # Non-instructors can only see published quizzes
        if not (self.request.user.role in ['mentor', 'administrator'] or self.request.user.is_staff):
            queryset = queryset.filter(is_published=True)
            
            # Filter out quizzes from subscription-required courses if user doesn't have a subscription
            if not getattr(self.request.user, 'has_subscription', False):
                queryset = queryset.filter(module__course__requires_subscription=False)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        quiz = self.get_object()
        
        # Validate the submission data
        serializer = QuizSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate the score
        answers = serializer.validated_data['answers']
        time_spent = serializer.validated_data['time_spent_seconds']
        score = quiz.calculate_score(answers)
        passed = score >= quiz.passing_score
        
        # Create a quiz attempt record
        attempt = UserQuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            score=score,
            passed=passed,
            completed_at=timezone.now(),
            time_spent_seconds=time_spent
        )
        
        # If passed, mark the module as completed
        if passed:
            progress, created = UserModuleProgress.objects.get_or_create(
                user=request.user,
                module=quiz.module
            )
            progress.mark_completed()
        
        return Response({
            'score': score,
            'passed': passed,
            'attempt_id': attempt.id
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def attempts(self, request, pk=None):
        quiz = self.get_object()
        attempts = UserQuizAttempt.objects.filter(
            user=request.user,
            quiz=quiz
        ).order_by('-started_at')
        
        serializer = UserQuizAttemptSerializer(attempts, many=True)
        return Response(serializer.data)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsInstructorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['quiz', 'question_type']
    ordering_fields = ['order']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return QuestionCreateUpdateSerializer
        return QuestionSerializer
    
    def get_queryset(self):
        queryset = Question.objects.all()
        
        # Non-instructors can only see questions from published quizzes
        if not (self.request.user.role in ['mentor', 'administrator'] or self.request.user.is_staff):
            queryset = queryset.filter(quiz__is_published=True)
            
            # Filter out questions from subscription-required courses if user doesn't have a subscription
            if not getattr(self.request.user, 'has_subscription', False):
                queryset = queryset.filter(quiz__module__course__requires_subscription=False)
        
        return queryset


class UserCourseProgressViewSet(viewsets.ModelViewSet):
    serializer_class = UserCourseProgressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrInstructor]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['course', 'is_completed']
    ordering_fields = ['started_at', 'last_activity', 'completed_at']
    
    def get_queryset(self):
        if self.request.user.role in ['mentor', 'administrator'] or self.request.user.is_staff:
            return UserCourseProgress.objects.all()
        return UserCourseProgress.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserModuleProgressViewSet(viewsets.ModelViewSet):
    serializer_class = UserModuleProgressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrInstructor]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['module', 'is_completed']
    ordering_fields = ['started_at', 'last_activity', 'completed_at']
    
    def get_queryset(self):
        if self.request.user.role in ['mentor', 'administrator'] or self.request.user.is_staff:
            return UserModuleProgress.objects.all()
        return UserModuleProgress.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserQuizAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserQuizAttemptSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrInstructor]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['quiz', 'passed']
    ordering_fields = ['started_at', 'completed_at', 'score']
    
    def get_queryset(self):
        if self.request.user.role in ['mentor', 'administrator'] or self.request.user.is_staff:
            return UserQuizAttempt.objects.all()
        return UserQuizAttempt.objects.filter(user=self.request.user)