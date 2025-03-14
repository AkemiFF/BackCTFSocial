# messaging/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone


class Channel(models.Model):
    """
    Represents a messaging channel (direct or group)
    """
    name = models.CharField(max_length=255, blank=True, null=True)
    is_group = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_channels',
        null=True
    )
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.is_group and self.name:
            return f"Group: {self.name}"
        return f"Channel {self.id}"
    
    def get_display_name(self, user):
        """
        Returns the display name for this channel from a user's perspective
        For direct messages, returns the other user's name
        For group chats, returns the group name
        """
        if self.is_group:
            return self.name or f"Group {self.id}"
        
        # For direct messages, get the other participant
        other_member = self.members.exclude(user=user).first()
        if other_member:
            return other_member.user.get_full_name() or other_member.user.username
        return f"Channel {self.id}"


class ChannelMember(models.Model):
    """
    Represents a member of a channel
    """
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('member', 'Member'),
    )
    
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='channel_memberships'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member'
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(default=timezone.now)
    is_muted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('channel', 'user')
        ordering = ['joined_at']
    
    def __str__(self):
        return f"{self.user.username} in {self.channel}"
    
    def mark_as_seen(self):
        """
        Update the last_seen_at timestamp to now
        """
        self.last_seen_at = timezone.now()
        self.save(update_fields=['last_seen_at'])


class Message(models.Model):
    """
    Represents a message in a channel
    """
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('code', 'Code'),
        ('system', 'System'),
    )
    
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messaging_sent_messages'
    )
    content = models.TextField()
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        default='text'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    
    # For attachments
    image = models.ImageField(upload_to='messages/images/', blank=True, null=True)
    file = models.FileField(upload_to='messages/files/', blank=True, null=True)
    
    # For code snippets
    code_language = models.CharField(max_length=50, blank=True, null=True)
    
    # For replies
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='replies',
        blank=True,
        null=True
    )
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender} in {self.channel}"
    
    def save(self, *args, **kwargs):
        # Mark as edited if it's an update
        if self.id:
            self.is_edited = True
        
        super().save(*args, **kwargs)
        
        # Update the channel's updated_at timestamp
        self.channel.save(update_fields=['updated_at'])


class ReadReceipt(models.Model):
    """
    Tracks which messages have been read by which users
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='read_receipts'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messaging_read_messages'
    )
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('message', 'user')
        ordering = ['read_at']
    
    def __str__(self):
        return f"{self.user.username} read {self.message}"


class Attachment(models.Model):
    """
    Represents an attachment to a message
    """
    ATTACHMENT_TYPES = (
        ('image', 'Image'),
        ('document', 'Document'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('other', 'Other'),
    )
    
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='messages/attachments/')
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # Size in bytes
    file_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES)
    content_type = models.CharField(max_length=100)  # MIME type
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.file_name} ({self.get_file_type_display()})"