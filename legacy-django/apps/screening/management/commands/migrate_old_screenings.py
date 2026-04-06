"""
Management command to link legacy screening results back to applications.
"""
from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.screening.models import ScreeningResult
from apps.applications.models import Application
from apps.assessments.models import SkillAssessmentAttempt


class Command(BaseCommand):
    help = 'Link screening results without applications to their originating applications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show which results would be migrated without saving changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Log each migration step',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        verbose = options.get('verbose', False)

        results = ScreeningResult.objects.filter(application__isnull=True).select_related(
            'resume', 'job', 'session__job'
        )
        total_to_process = results.count()
        self.stdout.write(self.style.SUCCESS(f'Found {total_to_process} results to migrate'))

        linked_count = 0
        skipped_count = 0

        for result in results:
            application = self._find_application_for_result(result)
            if not application:
                skipped_count += 1
                if verbose:
                    self.stdout.write(self.style.WARNING(
                        f'Could not link result {result.id}: no matching application'
                    ))
                continue

            linked_count += 1
            screening_answers = application.screening_answers or {}
            assessment_data = self._build_assessment_payload(application.applicant)

            if not dry_run:
                result.application = application
                result.screening_answers = screening_answers
                result.assessment_data = assessment_data
                result.save(update_fields=['application', 'screening_answers', 'assessment_data'])

            if verbose:
                self.stdout.write(self.style.SUCCESS(
                    f'Linked result {result.id} -> application {application.id}'
                ))

        self.stdout.write(self.style.SUCCESS(
            f'Successfully linked {linked_count} results to applications'
        ))
        self.stdout.write(self.style.WARNING(
            f'Could not link {skipped_count} results (no matching application)'
        ))

    def _find_application_for_result(self, result):
        """Try to locate the matching application for a legacy result."""
        candidate_email = None
        if result.resume and getattr(result.resume, 'user', None):
            candidate_email = result.resume.user.email

        job_id = result.job_id or getattr(result.session, 'job_id', None)

        if result.resume:
            app = Application.objects.filter(resume=result.resume).first()
            if app:
                return app

        if job_id and candidate_email:
            return Application.objects.filter(
                job_id=job_id,
                applicant__email__iexact=candidate_email
            ).first()

        if candidate_email:
            return Application.objects.filter(
                applicant__email__iexact=candidate_email
            ).first()

        return None

    def _build_assessment_payload(self, user):
        """Gather completed skill assessment attempts for the user."""
        attempts = SkillAssessmentAttempt.objects.filter(
            user=user,
            status='COMPLETED'
        ).select_related('test').order_by('-completed_at')

        payload = []
        for attempt in attempts:
            test = attempt.test
            skills = getattr(test, 'skills_tested', None) or []
            if skills is None:
                skills = []
            payload.append({
                'test_name': test.title if test else 'Unknown Test',
                'score': attempt.score,
                'passed': attempt.passed,
                'skills_validated': skills if isinstance(skills, list) else [skills],
                'completed_at': attempt.completed_at,
                'time_taken': getattr(attempt, 'time_taken_minutes', None) or getattr(attempt, 'time_taken', None),
            })
        return payload
