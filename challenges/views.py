# challenges/views.py
from django.db.models import Avg, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (Challenge, ChallengeCompletion, ChallengeRating, Hint,
                     Resource, Submission, UserHint)
from .permissions import IsChallengeCreatorOrReadOnly, IsOwnerOrStaff
from .serializers import (ChallengeCompletionSerializer,
                          ChallengeDetailSerializer, ChallengeRatingSerializer,
                          ChallengeSerializer, FlagSubmissionSerializer,
                          HintDetailSerializer, HintSerializer,
                          ResourceSerializer, SubmissionSerializer,
                          UserHintSerializer)


class ChallengeViewSet(viewsets.ModelViewSet):
    queryset = Challenge.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsChallengeCreatorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['difficulty', 'category', 'status', 'is_featured', 'requires_subscription']
    search_fields = ['title', 'description', 'tags__name']
    ordering_fields = ['title', 'created_at', 'points', 'difficulty']
    
    def get_serializer_class(self):
        if self.action in ['retrieve']:
            return ChallengeDetailSerializer
        return ChallengeSerializer
    
    def get_queryset(self):
        queryset = Challenge.objects.all()
        
        # Non-staff can only see published challenges
        if not (self.request.user.is_staff or self.request.user.role in ['administrator', 'moderator']):
            queryset = queryset.filter(status='published')
            
            # Filter out subscription-required challenges if user doesn't have a subscription
            if not getattr(self.request.user, 'has_subscription', False):
                queryset = queryset.filter(requires_subscription=False)
        
        # Filter by tag if provided
        tag = self.request.query_params.get('tag', None)
        if tag:
            queryset = queryset.filter(tags__name=tag)
        
        # Filter by completion status if provided
        completed = self.request.query_params.get('completed', None)
        if completed is not None:
            completed = completed.lower() == 'true'
            if completed:
                queryset = queryset.filter(completions__user=self.request.user)
            else:
                queryset = queryset.exclude(completions__user=self.request.user)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def submit_flag(self, request, pk=None):
        challenge = self.get_object()
        
        # Check if the challenge is published
        if challenge.status != 'published':
            return Response(
                {"detail": "This challenge is not available for submissions."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the challenge requires a subscription
        if challenge.requires_subscription and not getattr(request.user, 'has_subscription', False):
            return Response(
                {"detail": "This challenge requires a subscription."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if the user has already completed the challenge
        if ChallengeCompletion.objects.filter(user=request.user, challenge=challenge).exists():
            return Response(
                {"detail": "You have already completed this challenge."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the user has reached the maximum number of attempts
        if challenge.max_attempts:
            attempt_count = Submission.objects.filter(
                user=request.user,
                challenge=challenge
            ).count()
            
            if attempt_count >= challenge.max_attempts:
                return Response(
                    {"detail": f"You have reached the maximum number of attempts ({challenge.max_attempts})."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validate the submission data
        serializer = FlagSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Create the submission
        submitted_flag = serializer.validated_data['flag']
        time_spent = serializer.validated_data['time_spent_seconds']
        
        # Get hints used by the user
        hints_used = UserHint.objects.filter(
            user=request.user,
            challenge=challenge
        )
        
        submission = Submission.objects.create(
            user=request.user,
            challenge=challenge,
            submitted_flag=submitted_flag,
            is_correct=challenge.verify_flag(submitted_flag),
            time_spent_seconds=time_spent
        )
        
        # Add hints used to the submission
        submission.hints_used.set(hints_used.values_list('hint', flat=True))
        
        # If correct, create a challenge completion record
        if submission.is_correct:
            ChallengeCompletion.objects.create(
                user=request.user,
                challenge=challenge,
                points_earned=submission.points_awarded,
                time_spent_seconds=time_spent,
                attempts=Submission.objects.filter(
                    user=request.user,
                    challenge=challenge
                ).count()
            )
        
        return Response({
            'is_correct': submission.is_correct,
            'points_awarded': submission.points_awarded if submission.is_correct else 0,
            'attempt_number': submission.attempt_number
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def hints(self, request, pk=None):
        challenge = self.get_object()
        hints = challenge.hints.all().order_by('order')
        
        # Check if the user has unlocked any hints
        unlocked_hints = UserHint.objects.filter(
            user=request.user,
            challenge=challenge
        ).values_list('hint_id', flat=True)
        
        # Use different serializers for unlocked vs locked hints
        result = []
        for hint in hints:
            if hint.id in unlocked_hints:
                serializer = HintDetailSerializer(hint, context={'request': request})
            else:
                serializer = HintSerializer(hint, context={'request': request})
            result.append(serializer.data)
        
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def unlock_hint(self, request, pk=None):
        challenge = self.get_object()
        
        # Check if a hint_id was provided
        hint_id = request.data.get('hint_id')
        if not hint_id:
            return Response(
                {"detail": "hint_id is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the hint exists and belongs to this challenge
        try:
            hint = Hint.objects.get(id=hint_id, challenge=challenge)
        except Hint.DoesNotExist:
            return Response(
                {"detail": "Hint not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if the hint is already unlocked
        if UserHint.objects.filter(user=request.user, hint=hint).exists():
            return Response(
                {"detail": "You have already unlocked this hint."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the user has enough points
        if request.user.points < hint.cost:
            return Response(
                {"detail": f"You don't have enough points. This hint costs {hint.cost} points."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the UserHint record
        user_hint = UserHint.objects.create(
            user=request.user,
            challenge=challenge,
            hint=hint,
            points_deducted=hint.cost
        )
        
        # Deduct points from the user
        request.user.points -= hint.cost
        request.user.save(update_fields=['points'])
        
        # Return the hint content
        serializer = HintDetailSerializer(hint, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        challenge = self.get_object()
        
        # Check if the user has completed the challenge
        if not ChallengeCompletion.objects.filter(user=request.user, challenge=challenge).exists():
            return Response(
                {"detail": "You must complete the challenge before rating it."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate the rating data
        rating = request.data.get('rating')
        feedback = request.data.get('feedback', '')
        
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return Response(
                {"detail": "Rating must be an integer between 1 and 5."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or update the rating
        rating_obj, created = ChallengeRating.objects.update_or_create(
            user=request.user,
            challenge=challenge,
            defaults={
                'rating': rating,
                'feedback': feedback
            }
        )
        
        return Response({
            'id': rating_obj.id,
            'rating': rating_obj.rating,
            'feedback': rating_obj.feedback,
            'created_at': rating_obj.created_at
        }, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def completed(self, request):
        completions = ChallengeCompletion.objects.filter(
            user=request.user
        ).select_related('challenge')
        
        serializer = ChallengeCompletionSerializer(
            completions, 
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated, IsChallengeCreatorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['challenge', 'resource_type']
    
    def get_queryset(self):
        queryset = Resource.objects.all()
        
        # Non-staff can only see resources for published challenges
        if not (self.request.user.is_staff or self.request.user.role in ['administrator', 'moderator']):
            queryset = queryset.filter(challenge__status='published')
            
            # Filter out resources for subscription-required challenges if user doesn't have a subscription
            if not getattr(self.request.user, 'has_subscription', False):
                queryset = queryset.filter(challenge__requires_subscription=False)
        
        return queryset


class SubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['challenge', 'is_correct']
    ordering_fields = ['submission_time', 'points_awarded']
    
    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.role in ['administrator', 'moderator']:
            return Submission.objects.all()
        return Submission.objects.filter(user=self.request.user)


class UserHintViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserHintSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['challenge']
    ordering_fields = ['unlocked_at']
    
    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.role in ['administrator', 'moderator']:
            return UserHint.objects.all()
        return UserHint.objects.filter(user=self.request.user)


class ChallengeRatingViewSet(viewsets.ModelViewSet):
    serializer_class = ChallengeRatingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['challenge', 'rating']
    ordering_fields = ['created_at', 'rating']
    
    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.role in ['administrator', 'moderator']:
            return ChallengeRating.objects.all()
        return ChallengeRating.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChallengeCompletionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ChallengeCompletionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['challenge']
    ordering_fields = ['completed_at', 'points_earned', 'attempts']
    
    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.role in ['administrator', 'moderator']:
            return ChallengeCompletion.objects.all()
        return ChallengeCompletion.objects.filter(user=self.request.user)