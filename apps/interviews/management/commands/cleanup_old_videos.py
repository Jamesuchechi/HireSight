"""
Management command to clean up old practice videos based on retention policy.
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import default_storage

from apps.interviews.models import PracticeResponse, InterviewPracticeSession


class Command(BaseCommand):
    help = 'Delete old practice videos based on retention policy'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=None,
            help='Number of days to retain videos (overrides PRACTICE_VIDEO_RETENTION_DAYS setting)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt'
        )
    
    def handle(self, *args, **options):
        # Get retention days
        retention_days = options['days'] or getattr(settings, 'PRACTICE_VIDEO_RETENTION_DAYS', 30)
        dry_run = options['dry_run']
        force = options['force']
        
        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        self.stdout.write(
            f"Finding videos older than {retention_days} days (before {cutoff_date})"
        )
        
        # Find old responses with video data
        old_responses = PracticeResponse.objects.filter(
            created_at__lt=cutoff_date,
            video_analysis_metrics__isnull=False
        ).exclude(
            video_analysis_metrics={}
        )
        
        # Extract video file paths
        videos_to_delete = []
        for response in old_responses:
            metrics = response.video_analysis_metrics or {}
            video_file = metrics.get('video_file')
            
            if video_file:
                videos_to_delete.append({
                    'file': video_file,
                    'response_id': response.id,
                    'created_at': response.created_at,
                })
        
        if not videos_to_delete:
            self.stdout.write(self.style.SUCCESS('No videos found to delete'))
            return
        
        self.stdout.write(f"Found {len(videos_to_delete)} video(s) to delete")
        
        # Show what will be deleted
        self.stdout.write("\nVideos to be deleted:")
        for video_info in videos_to_delete:
            self.stdout.write(
                f"  - {video_info['file']} (Response {video_info['response_id']}, "
                f"created {video_info['created_at'].date()})"
            )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No files were actually deleted'))
            return
        
        # Ask for confirmation
        if not force:
            confirm = input(f"\nDelete {len(videos_to_delete)} video(s)? (y/n): ")
            if confirm.lower() != 'y':
                self.stdout.write(self.style.WARNING('Deletion cancelled'))
                return
        
        # Delete videos and update records
        deleted_count = 0
        failed_count = 0
        
        for video_info in videos_to_delete:
            try:
                # Delete from storage
                if default_storage.exists(video_info['file']):
                    default_storage.delete(video_info['file'])
                
                # Update response record
                response = PracticeResponse.objects.get(id=video_info['response_id'])
                metrics = response.video_analysis_metrics or {}
                metrics.pop('video_file', None)
                response.video_analysis_metrics = metrics
                response.save()
                
                deleted_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Deleted video {video_info['response_id']}")
                )
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f"✗ Failed to delete {video_info['response_id']}: {e}")
                )
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"Successfully deleted: {deleted_count}"))
        if failed_count:
            self.stdout.write(self.style.WARNING(f"Failed to delete: {failed_count}"))
        
        self.stdout.write(f"Total processed: {deleted_count + failed_count}")
        self.stdout.write(self.style.SUCCESS("Video cleanup completed!"))
        
        # Log this cleanup operation
        self._log_cleanup_operation(deleted_count, failed_count, retention_days)
    
    def _log_cleanup_operation(self, deleted_count, failed_count, retention_days):
        """Log the cleanup operation for audit purposes."""
        try:
            from apps.interviews.models import AIUsageLog
            
            AIUsageLog.objects.create(
                request_type='video_cleanup',
                model_used='maintenance',
                status='SUCCESS',
                notes=f'Deleted {deleted_count} videos (retention: {retention_days} days, {failed_count} failures)'
            )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not log operation: {e}"))
