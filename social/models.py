import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Post(models.Model):
    """User posts for the social feed."""
    
    POST_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('link', 'Link'),
        ('code', 'Code'),
        ('project', 'Project'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(_('content'))
    post_type = models.CharField(_('post type'), max_length=20, choices=POST_TYPES, default='text')
    image = models.ImageField(_('image'), upload_to='post_images/', blank=True, null=True)
    code_snippet = models.TextField(_('code snippet'), blank=True)
    code_language = models.CharField(_('code language'), max_length=50, blank=True)
    link_url = models.URLField(_('link URL'), blank=True)
    link_title = models.CharField(_('link title'), max_length=255, blank=True)
    link_description = models.TextField(_('link description'), blank=True)
    link_image = models.URLField(_('link image'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_edited = models.BooleanField(_('is edited'), default=False)
    is_pinned = models.BooleanField(_('is pinned'), default=False)
    is_public = models.BooleanField(_('is public'), default=True)
    tags = models.ManyToManyField('core.Tag', related_name='posts', blank=True)
    mentions = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='mentioned_in_posts', blank=True)
    
    class Meta:
        verbose_name = _('post')
        verbose_name_plural = _('posts')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s post - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_absolute_url(self):
        """Return the URL for this post."""
        return f"/posts/{self.id}/"
    
    def add_post(self):
        """Add a new post."""
        self.save()
    
    def edit_post(self, content):
        """Edit an existing post."""
        self.content = content
        self.is_edited = True
        self.updated_at = timezone.now()
        self.save()
    
    def delete_post(self):
        """Delete a post."""
        self.delete()
    
    @property
    def like_count(self):
        """Get the number of likes for this post."""
        return self.interactions.filter(interaction_type='like').count()
    
    @property
    def comment_count(self):
        """Get the number of comments for this post."""
        return self.comments.count()
    
    @property
    def share_count(self):
        """Get the number of shares for this post."""
        return self.interactions.filter(interaction_type='share').count()


class Comment(models.Model):
    """Comments on posts."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(_('content'))
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_edited = models.BooleanField(_('is edited'), default=False)
    mentions = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='mentioned_in_comments', blank=True)
    
    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.post}"
    
    def add_comment(self):
        """Add a new comment."""
        self.save()
    
    def edit_comment(self, content):
        """Edit an existing comment."""
        self.content = content
        self.is_edited = True
        self.updated_at = timezone.now()
        self.save()
    
    def delete_comment(self):
        """Delete a comment."""
        self.delete()
    
    @property
    def like_count(self):
        """Get the number of likes for this comment."""
        return self.interactions.filter(interaction_type='like').count()
    
    @property
    def is_reply(self):
        """Check if this comment is a reply to another comment."""
        return self.parent is not None


class SocialInteraction(models.Model):
    """Social interactions like likes, shares, etc."""
    
    INTERACTION_TYPES = (
        ('like', 'Like'),
        ('share', 'Share'),
        ('save', 'Save'),
        ('report', 'Report'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='social_interactions')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='interactions', null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='interactions', null=True, blank=True)
    interaction_type = models.CharField(_('interaction type'), max_length=20, choices=INTERACTION_TYPES)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('social interaction')
        verbose_name_plural = _('social interactions')
        unique_together = [
            ('user', 'post', 'interaction_type'),
            ('user', 'comment', 'interaction_type'),
        ]
    
    def __str__(self):
        target = self.post or self.comment
        return f"{self.user.username} {self.interaction_type}d {target}"
    
    def like_content(self):
        """Like a post or comment."""
        self.interaction_type = 'like'
        self.save()
    
    def share_content(self):
        """Share a post."""
        if not self.post:
            raise ValueError("Can only share posts, not comments")
        self.interaction_type = 'share'
        self.save()
    
    def save_content(self):
        """Save a post for later."""
        self.interaction_type = 'save'
        self.save()
    
    def report_content(self):
        """Report a post or comment."""
        self.interaction_type = 'report'
        self.save()


class Conversation(models.Model):
    """Private conversations between users."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_group = models.BooleanField(_('is group'), default=False)
    name = models.CharField(_('name'), max_length=255, blank=True)
    
    class Meta:
        verbose_name = _('conversation')
        verbose_name_plural = _('conversations')
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.is_group and self.name:
            return f"Group: {self.name}"
        participants = self.participants.all()
        if participants.count() <= 3:
            return ", ".join([user.username for user in participants])
        return f"{participants.first().username} and {participants.count() - 1} others"
    
    def get_absolute_url(self):
        """Return the URL for this conversation."""
        return f"/messages/{self.id}/"
    
    @property
    def last_message(self):
        """Get the last message in this conversation."""
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    """Messages within a conversation."""
    
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('code', 'Code'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(_('message type'), max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField(_('content'))
    image = models.ImageField(_('image'), upload_to='message_images/', blank=True, null=True)
    file = models.FileField(_('file'), upload_to='message_files/', blank=True, null=True)
    code_snippet = models.TextField(_('code snippet'), blank=True)
    code_language = models.CharField(_('code language'), max_length=50, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    is_read = models.BooleanField(_('is read'), default=False)
    read_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='read_messages', blank=True)
    
    class Meta:
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} in {self.conversation}"
    
    def mark_as_read(self, user):
        """Mark the message as read by a user."""
        if user != self.sender and user in self.conversation.participants.all():
            self.read_by.add(user)
            if self.read_by.count() == self.conversation.participants.count() - 1:
                self.is_read = True
                self.save()


class Project(models.Model):
    """User projects to showcase."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'))
    image = models.ImageField(_('image'), upload_to='project_images/', blank=True, null=True)
    repository_url = models.URLField(_('repository URL'), blank=True)
    demo_url = models.URLField(_('demo URL'), blank=True)
    technologies = models.ManyToManyField('core.Skill', related_name='projects', blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_public = models.BooleanField(_('is public'), default=True)
    
    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s project: {self.title}"
    
    def get_absolute_url(self):
        """Return the URL for this project."""
        return f"/projects/{self.id}/"