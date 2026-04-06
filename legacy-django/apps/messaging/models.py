# apps/messages/models.py
from django.db import models
from django.utils import timezone
from apps.accounts.models import User
from django.db.models import Q


class Conversation(models.Model):
    """
    Represents a conversation between two or more users.
    For HireSight, typically between a job seeker and a recruiter.
    """
    participants = models.ManyToManyField(
        User, 
        related_name='conversations',
        help_text="Users participating in this conversation"
    )
    subject = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Subject line for the conversation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Soft delete functionality
    is_archived = models.BooleanField(default=False)
    archived_by = models.ManyToManyField(
        User,
        related_name='archived_conversations',
        blank=True,
        help_text="Users who have archived this conversation"
    )
    
    # Related to job application (optional)
    related_job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        help_text="Optional: Link conversation to a specific job posting"
    )
    related_application = models.ForeignKey(
        'applications.Application',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        help_text="Optional: Link conversation to a specific application"
    )

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        participant_emails = [u.email for u in self.participants.all()[:3]]
        if self.participants.count() > 3:
            return f"Conversation: {', '.join(participant_emails)}..."
        return f"Conversation: {', '.join(participant_emails)}"

    def get_last_message(self):
        """Returns the most recent message in the conversation"""
        return self.messages.order_by('-timestamp').first()

    def get_unread_count(self, user):
        """Returns count of unread messages for a specific user"""
        return self.messages.filter(
            ~Q(sender=user),
            read_by__in=[user]
        ).exclude(
            read_by=user
        ).count()

    def mark_as_read(self, user):
        """Mark all messages in conversation as read for a user and return affected IDs"""
        unread_messages = list(
            self.messages.exclude(sender=user).exclude(read_by=user)
        )
        for message in unread_messages:
            message.read_by.add(user)
        return [message.id for message in unread_messages]

    def get_other_participant(self, current_user):
        """Get the other participant in a 1-on-1 conversation"""
        return self.participants.exclude(id=current_user.id).first()


class Message(models.Model):
    """
    Individual message within a conversation
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField(help_text="Message content")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Read status - many-to-many because multiple participants can read
    read_by = models.ManyToManyField(
        User,
        related_name='read_messages',
        blank=True,
        help_text="Users who have read this message"
    )
    
    # Edited message support
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Message type for system messages
    MESSAGE_TYPES = (
        ('user', 'User Message'),
        ('system', 'System Message'),
        ('template', 'Template Message'),
    )
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        default='user'
    )

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['conversation', 'timestamp']),
        ]

    def __str__(self):
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.sender.email}: {preview}"

    def mark_as_read(self, user):
        """Mark this message as read by a specific user"""
        if user != self.sender and user not in self.read_by.all():
            self.read_by.add(user)

    def is_read_by(self, user):
        """Check if message has been read by a specific user"""
        return user in self.read_by.all()


class MessageAttachment(models.Model):
    """
    File attachments for messages (images, PDFs, etc.)
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(
        upload_to='message_attachments/%Y/%m/%d/',
        help_text="Attached file"
    )
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)  # image/pdf/document
    file_size = models.IntegerField(help_text="File size in bytes")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Attachment: {self.filename}"

    def get_file_icon(self):
        """Return appropriate icon class based on file type"""
        if self.file_type.startswith('image/'):
            return 'fa-file-image'
        elif self.file_type == 'application/pdf':
            return 'fa-file-pdf'
        elif 'word' in self.file_type or 'document' in self.file_type:
            return 'fa-file-word'
        else:
            return 'fa-file'


class MessageTemplate(models.Model):
    """
    Pre-defined message templates for companies to send common responses
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='message_templates',
        limit_choices_to={'account_type': 'company'}
    )
    name = models.CharField(max_length=100, help_text="Template name")
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField(help_text="Template message content")
    
    # Template categories
    TEMPLATE_CATEGORIES = (
        ('screening', 'Screening Update'),
        ('interview', 'Interview Invitation'),
        ('rejection', 'Rejection Notice'),
        ('offer', 'Job Offer'),
        ('general', 'General Response'),
        ('followup', 'Follow-up'),
    )
    category = models.CharField(
        max_length=20,
        choices=TEMPLATE_CATEGORIES,
        default='general'
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Usage tracking
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-usage_count', 'name']
        unique_together = [['user', 'name']]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def increment_usage(self):
        """Increment usage count and update last used timestamp"""
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])


class BlockedUser(models.Model):
    """
    Tracks blocked users to prevent unwanted communication
    """
    blocker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blocked_users'
    )
    blocked = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blocked_by'
    )
    reason = models.TextField(blank=True)
    blocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['blocker', 'blocked']]
        indexes = [
            models.Index(fields=['blocker', 'blocked']),
        ]

    def __str__(self):
        return f"{self.blocker.email} blocked {self.blocked.email}"


class MessageReport(models.Model):
    """
    User reports for inappropriate messages
    """
    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='message_reports_made'
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    
    REPORT_REASONS = (
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('inappropriate', 'Inappropriate Content'),
        ('scam', 'Scam or Fraud'),
        ('other', 'Other'),
    )
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(blank=True)
    
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('action_taken', 'Action Taken'),
        ('dismissed', 'Dismissed'),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    reported_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-reported_at']
        unique_together = [['reporter', 'message']]

    def __str__(self):
        return f"Report by {self.reporter.email} - {self.get_reason_display()}"
