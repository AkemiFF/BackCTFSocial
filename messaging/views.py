# messaging/views.py
from django.db.models import Count, Max, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Attachment, Channel, ChannelMember, Message, ReadReceipt
from .permissions import IsChannelAdmin, IsChannelMember, IsMessageSender
from .serializers import (AttachmentSerializer, ChannelMemberSerializer,
                          ChannelSerializer, MessageSerializer,
                          ReadReceiptSerializer)


class ChannelViewSet(viewsets.ModelViewSet):
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated, IsChannelMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_group']
    ordering_fields = ['updated_at', 'created_at']
    
    def get_queryset(self):
        # Return channels where the user is a member
        return Channel.objects.filter(members__user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        channel = self.get_object()
        
        # Get messages for this channel
        messages = channel.messages.all().order_by('-created_at')
        
        # Filter by date range if provided
        since = request.query_params.get('since')
        if since:
            messages = messages.filter(created_at__gte=since)
        
        before = request.query_params.get('before')
        if before:
            messages = messages.filter(created_at__lt=before)
        
        # Paginate results
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        channel = self.get_object()
        
        # Get the user's membership
        try:
            membership = ChannelMember.objects.get(channel=channel, user=request.user)
        except ChannelMember.DoesNotExist:
            return Response(
                {"detail": "You are not a member of this channel."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update last_seen_at
        membership.mark_as_seen()
        
        # Create read receipts for all unread messages
        unread_messages = Message.objects.filter(
            channel=channel,
            created_at__gt=membership.last_seen_at
        ).exclude(sender=request.user)
        
        for message in unread_messages:
            ReadReceipt.objects.get_or_create(message=message, user=request.user)
        
        return Response(
            {"detail": f"Marked {unread_messages.count()} messages as read."},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        channel = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'member')
        
        # Validate role
        if role not in ['admin', 'member']:
            return Response(
                {"detail": "Invalid role. Must be 'admin' or 'member'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the current user is an admin
        if not channel.members.filter(user=request.user, role='admin').exists():
            return Response(
                {"detail": "Only channel admins can add members."},
                status=status.HTTP_403_FORBIDDEN
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
        
        # Check if the user is already a member
        if channel.members.filter(user=user).exists():
            return Response(
                {"detail": "User is already a member of this channel."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add the user to the channel
        membership = ChannelMember.objects.create(
            channel=channel,
            user=user,
            role=role
        )
        
        # Create a system message
        Message.objects.create(
            channel=channel,
            sender=None,
            content=f"{user.username} has joined the channel.",
            message_type='system'
        )
        
        serializer = ChannelMemberSerializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        channel = self.get_object()
        user_id = request.data.get('user_id')
        
        # Check if the current user is an admin
        if not channel.members.filter(user=request.user, role='admin').exists():
            return Response(
                {"detail": "Only channel admins can remove members."},
                status=status.HTTP_403_FORBIDDEN
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
        
        # Check if the user is a member
        try:
            membership = ChannelMember.objects.get(channel=channel, user=user)
        except ChannelMember.DoesNotExist:
            return Response(
                {"detail": "User is not a member of this channel."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Don't allow removing the last admin
        if membership.role == 'admin' and channel.members.filter(role='admin').count() <= 1:
            return Response(
                {"detail": "Cannot remove the last admin from the channel."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove the user from the channel
        membership.delete()
        
        # Create a system message
        Message.objects.create(
            channel=channel,
            sender=None,
            content=f"{user.username} has been removed from the channel.",
            message_type='system'
        )
        
        return Response(
            {"detail": f"{user.username} has been removed from the channel."},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        channel = self.get_object()
        
        # Check if the user is a member
        try:
            membership = ChannelMember.objects.get(channel=channel, user=request.user)
        except ChannelMember.DoesNotExist:
            return Response(
                {"detail": "You are not a member of this channel."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Don't allow leaving if the user is the last admin
        if membership.role == 'admin' and channel.members.filter(role='admin').count() <= 1:
            return Response(
                {"detail": "You are the last admin. Please promote another member to admin before leaving."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove the user from the channel
        membership.delete()
        
        # Create a system message
        Message.objects.create(
            channel=channel,
            sender=None,
            content=f"{request.user.username} has left the channel.",
            message_type='system'
        )
        
        return Response(
            {"detail": "You have left the channel."},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def direct(self, request):
        """
        Get or create a direct message channel with another user
        """
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            return Response(
                {"detail": "user_id query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the user exists
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if a direct channel already exists between these users
        # A direct channel has exactly 2 members and is not a group
        channels = Channel.objects.filter(
            is_group=False,
            members__user=request.user
        ).annotate(
            member_count=Count('members')
        ).filter(
            member_count=2,
            members__user=other_user
        )
        
        if channels.exists():
            # Return the existing channel
            channel = channels.first()
        else:
            # Create a new direct channel
            channel = Channel.objects.create(
                is_group=False,
                created_by=request.user
            )
            
            # Add both users as members
            ChannelMember.objects.create(
                channel=channel,
                user=request.user,
                role='admin'
            )
            
            ChannelMember.objects.create(
                channel=channel,
                user=other_user,
                role='admin'
            )
        
        serializer = self.get_serializer(channel)
        return Response(serializer.data)


class ChannelMemberViewSet(viewsets.ModelViewSet):
    serializer_class = ChannelMemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsChannelMember]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['channel', 'user', 'role']
    
    def get_queryset(self):
        # Return memberships for channels where the user is a member
        return ChannelMember.objects.filter(
            channel__members__user=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def change_role(self, request, pk=None):
        membership = self.get_object()
        role = request.data.get('role')
        
        # Validate role
        if role not in ['admin', 'member']:
            return Response(
                {"detail": "Invalid role. Must be 'admin' or 'member'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the current user is an admin of the channel
        if not membership.channel.members.filter(user=request.user, role='admin').exists():
            return Response(
                {"detail": "Only channel admins can change roles."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Don't allow demoting the last admin
        if membership.role == 'admin' and role == 'member':
            if membership.channel.members.filter(role='admin').count() <= 1:
                return Response(
                    {"detail": "Cannot demote the last admin."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Update the role
        membership.role = role
        membership.save(update_fields=['role'])
        
        # Create a system message
        Message.objects.create(
            channel=membership.channel,
            sender=None,
            content=f"{membership.user.username} is now a {role}.",
            message_type='system'
        )
        
        serializer = self.get_serializer(membership)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_mute(self, request, pk=None):
        membership = self.get_object()
        
        # Only allow users to mute/unmute their own memberships
        if membership.user != request.user:
            return Response(
                {"detail": "You can only mute/unmute your own memberships."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Toggle the mute status
        membership.is_muted = not membership.is_muted
        membership.save(update_fields=['is_muted'])
        
        serializer = self.get_serializer(membership)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsChannelMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['channel', 'sender', 'message_type']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        # Return messages from channels where the user is a member
        return Message.objects.filter(
            channel__members__user=self.request.user
        )
    
    def perform_create(self, serializer):
        message = serializer.save(sender=self.request.user)
        
        # Create a read receipt for the sender
        ReadReceipt.objects.create(
            message=message,
            user=self.request.user
        )
        
        return message
    
    def perform_update(self, serializer):
        # Only allow editing the content and attachments
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        message = self.get_object()
        
        # Create a read receipt
        receipt, created = ReadReceipt.objects.get_or_create(
            message=message,
            user=request.user
        )
        
        # Update the user's last_seen_at in the channel
        try:
            membership = ChannelMember.objects.get(
                channel=message.channel,
                user=request.user
            )
            if membership.last_seen_at < message.created_at:
                membership.mark_as_seen()
        except ChannelMember.DoesNotExist:
            pass
        
        return Response(
            {"detail": "Message marked as read."},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'])
    def mark_channel_read(self, request):
        channel_id = request.data.get('channel_id')
        
        if not channel_id:
            return Response(
                {"detail": "channel_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the channel exists and the user is a member
        try:
            channel = Channel.objects.get(id=channel_id)
            membership = ChannelMember.objects.get(
                channel=channel,
                user=request.user
            )
        except (Channel.DoesNotExist, ChannelMember.DoesNotExist):
            return Response(
                {"detail": "Channel not found or you are not a member."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update the user's last_seen_at
        membership.mark_as_seen()
        
        # Create read receipts for all unread messages
        unread_messages = Message.objects.filter(
            channel=channel,
            created_at__gt=membership.last_seen_at
        ).exclude(sender=request.user)
        
        for message in unread_messages:
            ReadReceipt.objects.get_or_create(
                message=message,
                user=request.user
            )
        
        return Response(
            {"detail": f"Marked {unread_messages.count()} messages as read."},
            status=status.HTTP_200_OK
        )


class ReadReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReadReceiptSerializer
    permission_classes = [permissions.IsAuthenticated, IsChannelMember]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['message', 'user']
    
    def get_queryset(self):
        # Return read receipts for messages in channels where the user is a member
        return ReadReceipt.objects.filter(
            message__channel__members__user=self.request.user
        )


class AttachmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsChannelMember]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['message', 'file_type']
    
    def get_queryset(self):
        # Return attachments for messages in channels where the user is a member
        return Attachment.objects.filter(
            message__channel__members__user=self.request.user
        )
