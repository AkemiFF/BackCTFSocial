import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Event(models.Model):
    """Base model for all types of events."""
    
    EVENT_TYPES = (
        ('ctf', 'Capture The Flag'),
        ('workshop', 'Workshop'),
        ('webinar', 'Webinar'),
        ('hackathon', 'Hackathon'),
        ('meetup', 'Meetup'),
        ('conference', 'Conference'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('registration_open', 'Registration Open'),
        ('registration_closed', 'Registration Closed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    event_type = models.CharField(_('event type'), max_length=20, choices=EVENT_TYPES)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateTimeField(_('start date'))
    end_date = models.DateTimeField(_('end date'))
    location = models.CharField(_('location'), max_length=255, blank=True)
    is_virtual = models.BooleanField(_('is virtual'), default=False)
    virtual_url = models.URLField(_('virtual URL'), blank=True)
    max_participants = models.PositiveIntegerField(_('maximum participants'), null=True, blank=True)
    registration_deadline = models.DateTimeField(_('registration deadline'), null=True, blank=True)
    image = models.ImageField(_('image'), upload_to='event_images/', blank=True, null=True)
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='organized_events')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_featured = models.BooleanField(_('is featured'), default=False)
    requires_subscription = models.BooleanField(_('requires subscription'), default=False)
    tags = models.ManyToManyField('accounts.Tag', related_name='events', blank=True)
    
    class Meta:
        verbose_name = _('event')
        verbose_name_plural = _('events')
        ordering = ['-start_date']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        """Return the URL for this event."""
        return f"/events/{self.id}/"
    
    @property
    def is_registration_open(self):
        """Check if registration is open for this event."""
        now = timezone.now()
        if self.registration_deadline and now > self.registration_deadline:
            return False
        if self.status != 'registration_open':
            return False
        if self.max_participants and self.registrations.count() >= self.max_participants:
            return False
        return True
    
    @property
    def is_ongoing(self):
        """Check if the event is currently ongoing."""
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    @property
    def is_past(self):
        """Check if the event has ended."""
        now = timezone.now()
        return now > self.end_date
    
    @property
    def participant_count(self):
        """Get the number of participants registered for this event."""
        return self.registrations.count()
    
    def update_status(self):
        """Update the event status based on current time and registrations."""
        now = timezone.now()
        
        if self.status == 'cancelled':
            return
        
        if now < self.start_date:
            if self.registration_deadline and now > self.registration_deadline:
                self.status = 'registration_closed'
            elif self.max_participants and self.registrations.count() >= self.max_participants:
                self.status = 'registration_closed'
            else:
                self.status = 'registration_open'
        elif self.start_date <= now <= self.end_date:
            self.status = 'in_progress'
        else:
            self.status = 'completed'
        
        self.save(update_fields=['status'])


class CTFEvent(models.Model):
    """Capture The Flag event model."""
    
    CTF_FORMATS = (
        ('jeopardy', 'Jeopardy'),
        ('attack_defense', 'Attack-Defense'),
        ('king_of_the_hill', 'King of the Hill'),
        ('mixed', 'Mixed'),
    )
    
    event = models.OneToOneField(Event, on_delete=models.CASCADE, primary_key=True, related_name='ctf_details')
    format = models.CharField(_('format'), max_length=20, choices=CTF_FORMATS, default='jeopardy')
    prize_pool = models.DecimalField(_('prize pool'), max_digits=10, decimal_places=2, null=True, blank=True)
    team_size = models.PositiveIntegerField(_('team size'), default=1)
    difficulty = models.CharField(_('difficulty'), max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ], default='intermediate')
    has_dynamic_scoring = models.BooleanField(_('has dynamic scoring'), default=False)
    scoreboard_visible = models.BooleanField(_('scoreboard visible'), default=True)
    
    class Meta:
        verbose_name = _('CTF event')
        verbose_name_plural = _('CTF events')
    
    def __str__(self):
        return f"CTF: {self.event.title}"


class Workshop(models.Model):
    """Workshop event model."""
    
    event = models.OneToOneField(Event, on_delete=models.CASCADE, primary_key=True, related_name='workshop_details')
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='workshops_as_instructor')
    prerequisites = models.TextField(_('prerequisites'), blank=True)
    materials = models.TextField(_('materials'), blank=True)
    difficulty = models.CharField(_('difficulty'), max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ], default='intermediate')
    has_certificate = models.BooleanField(_('has certificate'), default=False)
    
    class Meta:
        verbose_name = _('workshop')
        verbose_name_plural = _('workshops')
    
    def __str__(self):
        return f"Workshop: {self.event.title}"


class EventRegistration(models.Model):
    """User registration for an event."""
    
    STATUS_CHOICES = (
        ('registered', 'Registered'),
        ('confirmed', 'Confirmed'),
        ('attended', 'Attended'),
        ('cancelled', 'Cancelled'),
        ('waitlisted', 'Waitlisted'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_registrations')
    team = models.ForeignKey('teams.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='event_registrations')
    registration_date = models.DateTimeField(_('registration date'), auto_now_add=True)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='registered')
    notes = models.TextField(_('notes'), blank=True)
    check_in_time = models.DateTimeField(_('check-in time'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('event registration')
        verbose_name_plural = _('event registrations')
        unique_together = ('event', 'user')
        ordering = ['registration_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title}"
    
    def check_in(self):
        """Check in the user to the event."""
        if self.status in ['registered', 'confirmed', 'waitlisted']:
            self.status = 'attended'
            self.check_in_time = timezone.now()
            self.save(update_fields=['status', 'check_in_time'])
            return True
        return False
    
    def cancel(self):
        """Cancel the registration."""
        if self.status not in ['cancelled', 'attended']:
            self.status = 'cancelled'
            self.save(update_fields=['status'])
            
            # If there's a waitlist, move the next person up
            if self.event.max_participants:
                waitlisted = EventRegistration.objects.filter(
                    event=self.event,
                    status='waitlisted'
                ).order_by('registration_date').first()
                
                if waitlisted:
                    waitlisted.status = 'registered'
                    waitlisted.save(update_fields=['status'])
            
            return True
        return False


class EventFeedback(models.Model):
    """User feedback for an event."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_feedback')
    rating = models.PositiveSmallIntegerField(_('rating'), choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(_('comment'), blank=True)
    submitted_at = models.DateTimeField(_('submitted at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('event feedback')
        verbose_name_plural = _('event feedback')
        unique_together = ('event', 'user')
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.user.username}'s feedback for {self.event.title}"