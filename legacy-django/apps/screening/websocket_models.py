"""
WebSocket-related models for tracking operations and real-time events.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class BulkOperation(models.Model):
    """Track bulk operations for progress updates"""
    
    OPERATION_TYPES = [
        ('screen', 'Bulk Screening'),
        ('reject', 'Bulk Rejection'),
        ('move_pipeline', 'Bulk Move Pipeline'),
        ('export', 'Bulk Export'),
        ('email', 'Bulk Email'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bulk_operations')
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Progress tracking
    total_items = models.IntegerField(default=0)
    processed_items = models.IntegerField(default=0)
    failed_items = models.IntegerField(default=0)
    
    # Metadata
    description = models.TextField(blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    results = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.get_operation_type_display()} - {self.status}"
    
    def start(self):
        """Mark operation as started"""
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def complete(self):
        """Mark operation as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    def fail(self, error_message):
        """Mark operation as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'completed_at'])
    
    def update_progress(self, processed, failed=0):
        """Update operation progress"""
        self.processed_items = processed
        self.failed_items = failed
        self.save(update_fields=['processed_items', 'failed_items'])
    
    @property
    def progress_percentage(self):
        """Calculate progress percentage"""
        if self.total_items == 0:
            return 0
        return int((self.processed_items / self.total_items) * 100)
    
    @property
    def duration(self):
        """Get operation duration"""
        if not self.started_at:
            return None
        end = self.completed_at or timezone.now()
        return (end - self.started_at).total_seconds()
