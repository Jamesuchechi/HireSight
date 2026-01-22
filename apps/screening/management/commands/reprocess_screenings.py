"""
Management command to reprocess screening results and refresh match data.
"""
import uuid

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.screening.models import (
    ScreeningSession,
    ScreeningResultStatus,
    ScreeningStatus,
)
from apps.screening.tasks import process_resume_screening


STATUS_CHOICES = [choice[0] for choice in ScreeningResultStatus.choices]


class Command(BaseCommand):
    help = "Reprocess screening results (failed, pending, or completed) and queue them for scoring."

    def add_arguments(self, parser):
        parser.add_argument(
            "--session-id",
            type=str,
            help="Only reprocess results for a specific screening session.",
        )
        parser.add_argument(
            "--status",
            nargs="+",
            choices=STATUS_CHOICES + ["all"],
            default=["failed", "pending"],
            help="Filter results by status (can be repeated). Use 'all' to reprocess every result.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show which results would be reprocessed without updating them.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Maximum number of results to reprocess per session (0 = no limit).",
        )

    def handle(self, *args, **options):
        session_id = options.get("session_id")
        status_filters = options.get("status") or []
        dry_run = options.get("dry_run", False)
        limit = options.get("limit", 0)

        if "all" in status_filters:
            status_filters = STATUS_CHOICES

        sessions = ScreeningSession.objects.all().order_by("-created_at")
        if session_id:
            try:
                session_uuid = uuid.UUID(session_id.strip())
            except (ValueError, AttributeError):
                self.stdout.write(
                    self.style.ERROR(f"'{session_id}' is not a valid UUID.")
                )
                return
            sessions = ScreeningSession.objects.filter(id=session_uuid)

        if not sessions.exists():
            self.stdout.write(self.style.WARNING("No screening sessions found for the query."))
            return

        for session in sessions:
            self.stdout.write(self.style.SUCCESS(f"\n=== Session {session.title} ({session.id}) ==="))
            self.stdout.write(f"Status: {session.get_status_display()}, "
                              f"Total results: {session.total_resumes}")

            results = session.results.filter(status__in=status_filters).order_by("processed_at")
            if limit > 0:
                results = results[:limit]

            if not results.exists():
                self.stdout.write("No matching results to reprocess.")
                continue

            requeued = 0
            for result in results:
                self.stdout.write(f"- [{result.status}] result {result.id} (match_score={result.match_score})")
                if not dry_run:
                    if not (result.file_path or (result.resume and getattr(result.resume, "file", None))):
                        self.stdout.write(
                            self.style.WARNING("  ✗ Missing resume file path; skipping reprocess.")
                        )
                        continue

                    with transaction.atomic():
                        result.status = ScreeningResultStatus.PENDING
                        result.match_score = 0
                        result.match_details = {}
                        result.screening_answers = []
                        result.assessment_data = []
                        result.error_message = ""
                        result.processed_at = None
                        result.save(update_fields=[
                            "status",
                            "match_score",
                            "match_details",
                            "screening_answers",
                            "assessment_data",
                            "error_message",
                            "processed_at",
                        ])

                        # mark session as processing so UI reflects work happening
                        if session.status != ScreeningStatus.PROCESSING:
                            session.status = ScreeningStatus.PROCESSING
                            session.save(update_fields=["status"])

                    process_resume_screening.delay(result.id)
                    requeued += 1
                    self.stdout.write(self.style.SUCCESS("  ✓ Queued for reprocessing"))

            if dry_run:
                self.stdout.write(self.style.WARNING("Dry run: no queues were created."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Requeued {requeued} result(s) for session '{session.title}'"))
