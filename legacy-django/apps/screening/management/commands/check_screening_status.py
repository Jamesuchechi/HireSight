"""
Management command to check screening sessions and results status.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.screening.models import ScreeningSession, ScreeningResult, ScreeningStatus, ScreeningResultStatus
from apps.screening.tasks import process_resume_screening


class Command(BaseCommand):
    help = 'Check the status of screening sessions and identify issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--session-id',
            type=str,
            help='Check specific session by ID',
        )
        parser.add_argument(
            '--fix-stuck',
            action='store_true',
            help='Attempt to fix stuck screening sessions',
        )

    def handle(self, *args, **options):
        session_id = options.get('session_id')
        fix_stuck = options.get('fix_stuck', False)

        if session_id:
            self.check_specific_session(session_id, fix_stuck)
        else:
            self.check_all_sessions(fix_stuck)

    def check_specific_session(self, session_id, fix_stuck):
        """Check a specific screening session."""
        try:
            session = ScreeningSession.objects.get(id=session_id)
            self.stdout.write(self.style.SUCCESS(f'\n=== Session: {session.title} ({session.id}) ==='))
            self.print_session_details(session, fix_stuck)
        except ScreeningSession.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Session {session_id} not found'))

    def check_all_sessions(self, fix_stuck):
        """Check all screening sessions."""
        sessions = ScreeningSession.objects.all().order_by('-created_at')
        self.stdout.write(self.style.SUCCESS(f'\n=== All Screening Sessions ({sessions.count()}) ===\n'))
        
        for session in sessions:
            self.print_session_details(session, fix_stuck)

    def print_session_details(self, session, fix_stuck):
        """Print detailed info about a session."""
        self.stdout.write(f'\nSession: {session.title}')
        self.stdout.write(f'  Status: {session.get_status_display()}')
        self.stdout.write(f'  Created: {session.created_at}')
        self.stdout.write(f'  Total Resumes: {session.total_resumes}')
        self.stdout.write(f'  Processed: {session.processed_resumes}')
        self.stdout.write(f'  Failed: {session.failed_resumes}')
        self.stdout.write(f'  Pending: {session.total_resumes - session.processed_resumes - session.failed_resumes}')
        self.stdout.write(f'  Progress: {session.progress_percentage:.1f}%')
        self.stdout.write(f'  Avg Score: {session.average_match_score}')

        # Check criteria
        try:
            criteria = session.criteria
            self.stdout.write(f'  ✓ Criteria: CONFIGURED')
        except:
            self.stdout.write(self.style.WARNING(f'  ✗ Criteria: NOT FOUND'))

        # Check results status
        results = session.results.all()
        self.stdout.write(f'\n  Results Summary:')
        for status_choice in ScreeningResultStatus.choices:
            status = status_choice[0]
            count = results.filter(status=status).count()
            if count > 0:
                self.stdout.write(f'    {status.upper()}: {count}')

        # Check for stuck results (processing for too long)
        stuck_results = results.filter(status=ScreeningResultStatus.PROCESSING)
        if stuck_results.exists():
            self.stdout.write(self.style.WARNING(f'\n  ⚠ WARNING: {stuck_results.count()} results stuck in PROCESSING'))
            for result in stuck_results[:3]:  # Show first 3
                self.stdout.write(f'    - Result {result.id}')

        # Check for pending results
        pending_results = results.filter(status=ScreeningResultStatus.PENDING)
        if pending_results.exists():
            self.stdout.write(f'\n  ℹ Pending Results: {pending_results.count()}')
            if fix_stuck:
                self.stdout.write(self.style.SUCCESS('  Attempting to requeue pending results...'))
                for result in pending_results:
                    try:
                        if result.file_path:
                            process_resume_screening.delay(result.id)
                            self.stdout.write(f'    ✓ Requeued: {result.id}')
                        else:
                            self.stdout.write(self.style.ERROR(f'    ✗ No file_path: {result.id}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'    ✗ Error: {e}'))

        # Check for failed results
        failed_results = results.filter(status=ScreeningResultStatus.FAILED)
        if failed_results.exists():
            self.stdout.write(f'\n  ✗ Failed Results: {failed_results.count()}')
            for result in failed_results[:3]:  # Show first 3
                self.stdout.write(f'    - Result {result.id}')
                if result.error_message:
                    self.stdout.write(f'      Error: {result.error_message[:100]}')
