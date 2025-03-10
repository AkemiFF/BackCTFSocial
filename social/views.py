# social/views.py
from django.db.models import Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (Comment, Conversation, Message, Post, Project,
                     SocialInteraction)
from .permissions import (IsOwnerOrReadOnly, IsParticipantOrAdmin,
                          IsPublicOrOwner)
from .serializers import (CommentSerializer, ConversationSerializer,
                          MessageSerializer, PostSerializer, ProjectSerializer,
                          SocialInteractionSerializer)


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['post_type', 'user', 'is_pinned', 'is_public']
    search_fields = ['content', 'tags__name']
    ordering_fields = ['created_at', 'updated_at', 'like_count']
    
    def get_queryset(self):
        queryset = Post.objects.all()
        
        # Filter for public posts or user's own posts
        if not (self.request.user.is_staff or self.request.user.role == 'administrator'):
            queryset = queryset.filter(
                Q(is_public=True) | Q(user=self.request.user)
            )
        
        # Filter by tag if provided
        tag = self.request.query_params.get('tag', None)
        if tag:
            queryset = queryset.filter(tags__name=tag)
        
        # Add like count annotation for ordering
        queryset = queryset.annotate(
            like_count=Count('interactions', filter=Q(interactions__interaction_type='like'))
        )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        post = self.get_object()
        
        # Create or get the like interaction
        interaction, created = SocialInteraction.objects.get_or_create(
            user=request.user,
            post=post,
            interaction_type='like'
        )
        
        if created:
            return Response(
                {"detail": "Post liked successfully."}, 
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"detail": "You have already liked this post."}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        post = self.get_object()
        
        # Find and delete the like interaction
        try:
            interaction = SocialInteraction.objects.get(
                user=request.user,
                post=post,
                interaction_type='like'
            )
            interaction.delete()
            return Response(
                {"detail": "Post unliked successfully."}, 
                status=status.HTTP_200_OK
            )
        except SocialInteraction.DoesNotExist:
            return Response(
                {"detail": "You have not liked this post."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def save(self, request, pk=None):
        post = self.get_object()
        
        # Create or get the save interaction
        interaction, created = SocialInteraction.objects.get_or_create(
            user=request.user,
            post=post,
            interaction_type='save'
        )
        
        if created:
            return Response(
                {"detail": "Post saved successfully."}, 
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"detail": "You have already saved this post."}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def unsave(self, request, pk=None):
        post = self.get_object()
        
        # Find and delete the save interaction
        try:
            interaction = SocialInteraction.objects.get(
                user=request.user,
                post=post,
                interaction_type='save'
            )
            interaction.delete()
            return Response(
                {"detail": "Post unsaved successfully."}, 
                status=status.HTTP_200_OK
            )
        except SocialInteraction.DoesNotExist:
            return Response(
                {"detail": "You have not saved this post."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        post = self.get_object()
        
        # Create the share interaction
        interaction = SocialInteraction.objects.create(
            user=request.user,
            post=post,
            interaction_type='share'
        )
        
        return Response(
            {"detail": "Post shared successfully."}, 
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        post = self.get_object()
        reason = request.data.get('reason', '')
        
        # Create the report interaction
        interaction, created = SocialInteraction.objects.get_or_create(
            user=request.user,
            post=post,
            interaction_type='report'
        )
        
        # TODO: Notify moderators about the report
        
        return Response(
            {"detail": "Post reported successfully."}, 
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        post = self.get_object()
        
        # Get only top-level comments (no replies)
        comments = post.comments.filter(parent=None).order_by('-created_at')
        
        page = self.paginate_queryset(comments)
        if page is not None:
            serializer = CommentSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def feed(self, request):
        # Get posts from users the current user follows
        from accounts.models import UserFollowing
        
        following_users = UserFollowing.objects.filter(
            user=request.user
        ).values_list('following_user', flat=True)
        
        # Include the user's own posts and posts from followed users
        queryset = Post.objects.filter(
            Q(user=request.user) | Q(user__in=following_users),
            is_public=True
        ).order_by('-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def saved(self, request):
        # Get posts saved by the current user
        saved_posts = Post.objects.filter(
            interactions__user=request.user,
            interactions__interaction_type='save'
        ).order_by('-interactions__created_at')
        
        page = self.paginate_queryset(saved_posts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(saved_posts, many=True)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['post', 'user', 'parent']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        return Comment.objects.all()
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        comment = self.get_object()
        
        # Create or get the like interaction
        interaction, created = SocialInteraction.objects.get_or_create(
            user=request.user,
            comment=comment,
            interaction_type='like'
        )
        
        if created:
            return Response(
                {"detail": "Comment liked successfully."}, 
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"detail": "You have already liked this comment."}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        comment = self.get_object()
        
        # Find and delete the like interaction
        try:
            interaction = SocialInteraction.objects.get(
                user=request.user,
                comment=comment,
                interaction_type='like'
            )
            interaction.delete()
            return Response(
                {"detail": "Comment unliked successfully."}, 
                status=status.HTTP_200_OK
            )
        except SocialInteraction.DoesNotExist:
            return Response(
                {"detail": "You have not liked this comment."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        comment = self.get_object()
        reason = request.data.get('reason', '')
        
        # Create the report interaction
        interaction, created = SocialInteraction.objects.get_or_create(
            user=request.user,
            comment=comment,
            interaction_type='report'
        )
        
        # TODO: Notify moderators about the report
        
        return Response(
            {"detail": "Comment reported successfully."}, 
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        comment = self.get_object()
        
        # Get replies to this comment
        replies = comment.replies.all().order_by('created_at')
        
        page = self.paginate_queryset(replies)
        if page is not None:
            serializer = CommentSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = CommentSerializer(replies, many=True, context={'request': request})
        return Response(serializer.data)


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated, IsParticipantOrAdmin]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['updated_at']
    
    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.role == 'administrator':
            return Conversation.objects.all()
        return Conversation.objects.filter(participants=self.request.user)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        
        # Get messages for this conversation
        messages = conversation.messages.all().order_by('created_at')
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {"detail": "user_id is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the user exists
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Add the user to the conversation
        conversation.participants.add(user)
        
        return Response(
            {"detail": f"{user.username} added to the conversation."}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {"detail": "user_id is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the user exists
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if the user is a participant
        if user not in conversation.participants.all():
            return Response(
                {"detail": f"{user.username} is not a participant in this conversation."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove the user from the conversation
        conversation.participants.remove(user)
        
        return Response(
            {"detail": f"{user.username} removed from the conversation."}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        conversation = self.get_object()
        
        # Remove the current user from the conversation
        conversation.participants.remove(request.user)
        
        return Response(
            {"detail": "You have left the conversation."}, 
            status=status.HTTP_200_OK
        )


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsParticipantOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['conversation', 'sender', 'message_type', 'is_read']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.role == 'administrator':
            return Message.objects.all()
        return Message.objects.filter(conversation__participants=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        message = self.get_object()
        
        # Mark the message as read by the current user
        message.mark_as_read(request.user)
        
        return Response(
            {"detail": "Message marked as read."}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'])
    def mark_conversation_read(self, request):
        conversation_id = request.data.get('conversation_id')
        
        if not conversation_id:
            return Response(
                {"detail": "conversation_id is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the conversation exists and the user is a participant
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            if request.user not in conversation.participants.all():
                return Response(
                    {"detail": "You are not a participant in this conversation."}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except Conversation.DoesNotExist:
            return Response(
                {"detail": "Conversation not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Mark all messages in the conversation as read by the current user
        unread_messages = Message.objects.filter(
            conversation=conversation,
            sender__ne=request.user
        ).exclude(read_by=request.user)
        
        for message in unread_messages:
            message.mark_as_read(request.user)
        
        return Response(
            {"detail": f"Marked {unread_messages.count()} messages as read."}, 
            status=status.HTTP_200_OK
        )


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsPublicOrOwner]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'is_public', 'technologies']
    search_fields = ['title', 'description', 'technologies__name']
    ordering_fields = ['created_at', 'updated_at', 'title']
    
    def get_queryset(self):
        queryset = Project.objects.all()
        
        # Filter for public projects or user's own projects
        if not (self.request.user.is_staff or self.request.user.role == 'administrator'):
            queryset = queryset.filter(
                Q(is_public=True) | Q(user=self.request.user)
            )
        
        return queryset


class SocialInteractionViewSet(viewsets.ModelViewSet):
    serializer_class = SocialInteractionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['interaction_type', 'post', 'comment']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.role == 'administrator':
            return SocialInteraction.objects.all()
        return SocialInteraction.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)