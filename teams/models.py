import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Team(models.Model):
    """Team model for collaborative work and challenges."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    logo = models.ImageField(_('logo'), upload_to='team_logos/', blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_public = models.BooleanField(_('is public'), default=True)
    website = models.URLField(_('website'), blank=True)
    github_url = models.URLField(_('GitHub URL'), blank=True)
    discord_url = models.URLField(_('Discord URL'), blank=True)
    max_members = models.PositiveIntegerField(_('maximum members'), default=10)
    tags = models.ManyToManyField('core.Tag', related_name='teams', blank=True)
    
    class Meta:
        verbose_name = _('team')
        verbose_name_plural = _('teams')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        """Return the URL for this team."""
        return f"/teams/{self.id}/"
    
    @property
    def member_count(self):
        """Get the number of members in the team."""
        return self.memberships.count()
    
    @property
    def leader(self):
        """Get the team leader."""
        leader_membership = self.memberships.filter(role='leader').first()
        return leader_membership.user if leader_membership else None
    
    @property
    def total_points(self):
        """Calculate the total points earned by the team."""
        from gamification.models import Score
        return Score.objects.filter(team=self).aggregate(models.Sum('points'))['points__sum'] or 0
    
    def add_member(self, user, role='member'):
        """Add a user to the team."""
        if self.memberships.count() >= self.max_members:
            raise ValueError(_("Team has reached maximum member capacity"))
        
        if not self.memberships.filter(user=user).exists():
            TeamMembership.objects.create(team=self, user=user, role=role)
            return True
        return False
    
    def remove_member(self, user):
        """Remove a user from the team."""
        membership = self.memberships.filter(user=user).first()
        if membership:
            if membership.role == 'leader' and self.memberships.count() > 1:
                # Promote another member to leader before removing the current leader
                new_leader = self.memberships.exclude(user=user).first()
                new_leader.role = 'leader'
                new_leader.save()
            
            membership.delete()
            return True
        return False


class TeamMembership(models.Model):
    """Membership of a user in a team."""
    
    ROLE_CHOICES = (
        ('leader', 'Leader'),
        ('co-leader', 'Co-Leader'),
        ('member', 'Member'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='team_memberships')
    role = models.CharField(_('role'), max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(_('joined at'), auto_now_add=True)
    contribution_points = models.PositiveIntegerField(_('contribution points'), default=0)
    
    class Meta:
        verbose_name = _('team membership')
        verbose_name_plural = _('team memberships')
        unique_together = ('team', 'user')
        ordering = ['team', 'role', 'joined_at']
    
    def __str__(self):
        return f"{self.user.username} in {self.team.name} as {self.get_role_display()}"
    
    def promote(self):
        """Promote the member to the next role level."""
        if self.role == 'member':
            self.role = 'co-leader'
            self.save()
            return True
        elif self.role == 'co-leader':
            # Check if there's already a leader
            current_leader = self.team.memberships.filter(role='leader').first()
            if current_leader:
                current_leader.role = 'co-leader'
                current_leader.save()
            
            self.role = 'leader'
            self.save()
            return True
        return False
    
    def demote(self):
        """Demote the member to the previous role level."""
        if self.role == 'leader':
            # Must have another member to take leadership
            potential_leader = self.team.memberships.exclude(id=self.id).first()
            if potential_leader:
                potential_leader.role = 'leader'
                potential_leader.save()
                
                self.role = 'co-leader'
                self.save()
                return True
            return False
        elif self.role == 'co-leader':
            self.role = 'member'
            self.save()
            return True
        return False


class TeamInvitation(models.Model):
    """Invitation to join a team."""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='invitations')
    inviter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_team_invitations')
    invitee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_team_invitations')
    message = models.TextField(_('message'), blank=True)
    role = models.CharField(_('role'), max_length=20, choices=TeamMembership.ROLE_CHOICES, default='member')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'))
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    class Meta:
        verbose_name = _('team invitation')
        verbose_name_plural = _('team invitations')
        unique_together = ('team', 'invitee', 'status')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invitation for {self.invitee.username} to join {self.team.name}"
    
    def save(self, *args, **kwargs):
        """Set expiration date if not provided."""
        if not self.expires_at:
            # Default expiration is 7 days from creation
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)
    
    def accept(self):
        """Accept the invitation and add the user to the team."""
        if self.status != 'pending':
            return False
        
        if timezone.now() > self.expires_at:
            self.status = 'expired'
            self.save()
            return False
        
        # Add the user to the team
        success = self.team.add_member(self.invitee, self.role)
        if success:
            self.status = 'accepted'
            self.save()
            return True
        return False
    
    def decline(self):
        """Decline the invitation."""
        if self.status != 'pending':
            return False
        
        self.status = 'declined'
        self.save()
        return True
    
    @property
    def is_expired(self):
        """Check if the invitation has expired."""
        return timezone.now() > self.expires_at
    
    def check_expiry(self):
        """Check and update the status if the invitation has expired."""
        if self.status == 'pending' and self.is_expired:
            self.status = 'expired'
            self.save()
            return True
        return False


class TeamJoinRequest(models.Model):
    """Request to join a team."""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='join_requests')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='team_join_requests')
    message = models.TextField(_('message'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'))
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    class Meta:
        verbose_name = _('team join request')
        verbose_name_plural = _('team join requests')
        unique_together = ('team', 'user', 'status')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Request from {self.user.username} to join {self.team.name}"
    
    def save(self, *args, **kwargs):
        """Set expiration date if not provided."""
        if not self.expires_at:
            # Default expiration is 7 days from creation
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)
    
    def accept(self):
        """Accept the request and add the user to the team."""
        if self.status != 'pending':
            return False
        
        if timezone.now() > self.expires_at:
            self.status = 'expired'
            self.save()
            return False
        
        # Add the user to the team
        success = self.team.add_member(self.user)
        if success:
            self.status = 'accepted'
            self.save()
            return True
        return False
    
    def decline(self):
        """Decline the request."""
        if self.status != 'pending':
            return False
        
        self.status = 'declined'
        self.save()
        return True
    
    @property
    def is_expired(self):
        """Check if the request has expired."""
        return timezone.now() > self.expires_at
    
    def check_expiry(self):
        """Check and update the status if the request has expired."""
        if self.status == 'pending' and self.is_expired:
            self.status = 'expired'
            self.save()
            return True
        return False