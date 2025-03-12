# messaging/serializers.py
from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Attachment, Channel, ChannelMember, Message, ReadReceipt


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'file', 'file_name', 'file_size', 'file_type', 'content_type', 'created_at']
        read_only_fields = ['id', 'file_name', 'file_size', 'content_type', 'created_at']


class ReadReceiptSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = ReadReceipt
        fields = ['id', 'user', 'user_details', 'read_at']
        read_only_fields = ['id', 'user', 'read_at']


class MessageSerializer(serializers.ModelSerializer):
    sender_details = UserSerializer(source='sender', read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    read_by = serializers.SerializerMethodField()
    reply_to_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'channel', 'sender', 'sender_details', 'content', 'message_type',
                  'created_at', 'updated_at', 'is_edited', 'image', 'file',
                  'code_language', 'reply_to', 'reply_to_details', 'attachments', 'read_by']
        read_only_fields = ['id', 'sender', 'created_at', 'updated_at', 'is_edited']
    
    def get_read_by(self, obj):
        return ReadReceiptSerializer(obj.read_receipts.all(), many=True).data
    
    def get_reply_to_details(self, obj):
        if not obj.reply_to:
            return None
        
        return {
            'id': obj.reply_to.id,
            'content': obj.reply_to.content[:100],  # Truncate long content
            'sender': obj.reply_to.sender.username if obj.reply_to.sender else None,
            'message_type': obj.reply_to.message_type
        }
    
    def create(self, validated_data):
        # Add the sender from the request
        validated_data['sender'] = self.context['request'].user
        
        # Create the message
        message = Message.objects.create(**validated_data)
        
        # Handle attachments
        request = self.context.get('request')
        if request and request.FILES:
            for file_key in request.FILES:
                file_obj = request.FILES[file_key]
                
                # Determine file type based on content type
                content_type = file_obj.content_type
                if content_type.startswith('image/'):
                    file_type = 'image'
                elif content_type.startswith('audio/'):
                    file_type = 'audio'
                elif content_type.startswith('video/'):
                    file_type = 'video'
                elif content_type.startswith('application/') or content_type.startswith('text/'):
                    file_type = 'document'
                else:
                    file_type = 'other'
                
                # Create attachment
                Attachment.objects.create(
                    message=message,
                    file=file_obj,
                    file_name=file_obj.name,
                    file_size=file_obj.size,
                    file_type=file_type,
                    content_type=content_type
                )
        
        return message


class ChannelMemberSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChannelMember
        fields = ['id', 'channel', 'user', 'user_details', 'role', 'joined_at',
                  'last_seen_at', 'is_muted', 'unread_count']
        read_only_fields = ['id', 'joined_at', 'last_seen_at']
    
    def get_unread_count(self, obj):
        # Count messages in the channel that were created after the user's last_seen_at
        return Message.objects.filter(
            channel=obj.channel,
            created_at__gt=obj.last_seen_at
        ).count()


class ChannelSerializer(serializers.ModelSerializer):
    members_details = ChannelMemberSerializer(source='members', many=True, read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)
    last_message = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Channel
        fields = ['id', 'name', 'is_group', 'created_at', 'updated_at',
                  'created_by', 'created_by_details', 'members_details',
                  'last_message', 'display_name', 'unread_count']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if not last_msg:
            return None
        
        return {
            'id': last_msg.id,
            'content': last_msg.content[:100],  # Truncate long content
            'sender': last_msg.sender.username if last_msg.sender else 'System',
            'created_at': last_msg.created_at,
            'message_type': last_msg.message_type
        }
    
    def get_display_name(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return obj.name or f"Channel {obj.id}"
        
        return obj.get_display_name(request.user)
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        
        try:
            membership = ChannelMember.objects.get(channel=obj, user=request.user)
            return Message.objects.filter(
                channel=obj,
                created_at__gt=membership.last_seen_at
            ).count()
        except ChannelMember.DoesNotExist:
            return 0
    
    def create(self, validated_data):
        # Add the created_by from the request
        validated_data['created_by'] = self.context['request'].user
        
        # Get members data
        members_data = self.context['request'].data.get('members', [])
        
        # Create the channel
        channel = Channel.objects.create(**validated_data)
        
        # Add the creator as an admin member
        ChannelMember.objects.create(
            channel=channel,
            user=validated_data['created_by'],
            role='admin'
        )
        
        
        # Add other members
        for member_id in members_data:
            if member_id != validated_data['created_by'].id:
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    user = User.objects.get(id=member_id)
                    ChannelMember.objects.create(
                        channel=channel,
                        user=user,
                        role='member'
                    )
                except User.DoesNotExist:
                    pass
        
        return channel