"""
Django management command to verify and fix job slugs.

Save this file as: apps/jobs/management/commands/fix_job_slugs.py

Usage:
    python manage.py fix_job_slugs
    python manage.py fix_job_slugs --check-only
    python manage.py fix_job_slugs --job-id=b3af0189-0c1c-4b51-b001-99e07204cb14
"""

from django.core.management.base import BaseCommand
from apps.jobs.models import Job


class Command(BaseCommand):
    help = 'Verify and fix job slugs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check for issues without fixing',
        )
        parser.add_argument(
            '--job-id',
            type=str,
            help='Check/fix specific job by UUID',
        )

    def handle(self, *args, **options):
        check_only = options['check_only']
        job_id = options.get('job_id')

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Job Slug Verification and Fix Tool'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        if job_id:
            # Check specific job
            self.check_specific_job(job_id, check_only)
        else:
            # Check all jobs
            self.check_all_jobs(check_only)

    def check_specific_job(self, job_id, check_only):
        """Check a specific job by UUID."""
        try:
            job = Job.objects.get(id=job_id)
            self.stdout.write(f"\n✅ Job found:")
            self.stdout.write(f"   ID:    {job.id}")
            self.stdout.write(f"   Title: {job.title}")
            self.stdout.write(f"   Slug:  {job.slug}")
            
            if job.slug:
                self.stdout.write(self.style.SUCCESS(f"\n✅ Job has a valid slug: {job.slug}"))
                self.stdout.write(f"\n🔗 URL: /jobs/{job.slug}/")
            else:
                self.stdout.write(self.style.ERROR(f"\n❌ Job has no slug!"))
                
                if not check_only:
                    self.stdout.write("\n🔧 Generating slug...")
                    job.save()  # This will trigger slug generation
                    self.stdout.write(self.style.SUCCESS(f"   ✅ Generated slug: {job.slug}"))
                    self.stdout.write(f"   🔗 URL: /jobs/{job.slug}/")
                else:
                    self.stdout.write("\n   Run without --check-only to fix")

        except Job.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"\n❌ Job with ID {job_id} not found in database"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error: {e}"))

    def check_all_jobs(self, check_only):
        """Check all jobs for slug issues."""
        total_jobs = Job.objects.count()
        self.stdout.write(f"\n📊 Total jobs in database: {total_jobs}")

        # Find jobs without slugs
        jobs_without_slug = Job.objects.filter(slug__isnull=True) | Job.objects.filter(slug='')
        problem_count = jobs_without_slug.count()

        if problem_count == 0:
            self.stdout.write(self.style.SUCCESS("\n✅ All jobs have valid slugs!"))
            self.show_sample_jobs()
            return

        self.stdout.write(self.style.WARNING(f"\n⚠️  Found {problem_count} job(s) without slugs:"))
        self.stdout.write("")

        for job in jobs_without_slug[:10]:  # Show first 10
            self.stdout.write(f"   - {job.title} (ID: {job.id})")

        if problem_count > 10:
            self.stdout.write(f"   ... and {problem_count - 10} more")

        if not check_only:
            self.stdout.write(f"\n🔧 Fixing {problem_count} job(s)...")
            fixed = 0
            
            for job in jobs_without_slug:
                try:
                    job.save()  # Trigger slug generation
                    fixed += 1
                    self.stdout.write(f"   ✅ {job.title} -> {job.slug}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"   ❌ Failed to fix {job.title}: {e}"))

            self.stdout.write(self.style.SUCCESS(f"\n✅ Fixed {fixed} out of {problem_count} job(s)"))
        else:
            self.stdout.write("\n💡 Run without --check-only to fix these issues")

        self.show_sample_jobs()

    def show_sample_jobs(self):
        """Show sample jobs with their URLs."""
        sample_jobs = Job.objects.all()[:5]
        
        if sample_jobs:
            self.stdout.write("\n📝 Sample job URLs:")
            for job in sample_jobs:
                self.stdout.write(f"\n   {job.title}")
                self.stdout.write(f"   - By slug: /jobs/{job.slug}/")
                self.stdout.write(f"   - By ID:   /jobs/by-id/{job.id}/")