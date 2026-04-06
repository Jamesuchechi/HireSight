from django.core.management.base import BaseCommand
from django.conf import settings
import importlib
import sys

class Command(BaseCommand):
    help = 'Validate practice settings: AI keys, storage access, and rate limits.'

    def handle(self, *args, **options):
        self.stdout.write('Validating practice settings...')
        failures = 0

        # Check AI keys
        ai_keys = [
            'INTERVIEW_PRACTICE_MISTRAL_API_KEY',
            'MISTRAL_AI_API_KEY',
            'OPENAI_API_KEY',
            'GOOGLE_API_KEY'
        ]

        self.stdout.write('\nChecking AI keys:')
        for k in ai_keys:
            if getattr(settings, k, None):
                self.stdout.write(f' - {k}: OK')
            else:
                self.stdout.write(f' - {k}: MISSING')
                failures += 1

        # Check storage (S3) accessibility if configured
        default_storage = getattr(settings, 'DEFAULT_FILE_STORAGE', '')
        bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None) or getattr(settings, 'AWS_S3_BUCKET_NAME', None)

        self.stdout.write('\nChecking storage settings:')
        if 's3' in default_storage.lower() or bucket_name:
            try:
                import boto3
                s3 = boto3.client('s3')
                if not bucket_name:
                    self.stdout.write(' - AWS bucket name not configured')
                    failures += 1
                else:
                    try:
                        s3.head_bucket(Bucket=bucket_name)
                        self.stdout.write(f' - S3 bucket "{bucket_name}": accessible')
                    except Exception as e:
                        self.stdout.write(f' - S3 bucket "{bucket_name}": NOT accessible: {e}')
                        failures += 1
            except Exception as e:
                self.stdout.write(' - boto3 not installed; cannot verify S3 bucket')
                failures += 1
        else:
            self.stdout.write(' - Using local or other file storage; skipping S3 checks')

        # Test AI connectivity (optional; will attempt a lightweight call if connector exists)
        self.stdout.write('\nTesting AI connector availability:')
        try:
            ai_module = importlib.import_module('apps.interviews.ai')
            if hasattr(ai_module, '_safe_call'):
                try:
                    # Try a dry-run call only if key present
                    test_payload = {'input': 'hello', 'temperature': 0}
                    try:
                        ai_module._safe_call(test_payload)
                        self.stdout.write(' - AI connector: able to make request (check logs for details)')
                    except Exception as e:
                        self.stdout.write(f' - AI connector request failed: {e}')
                        failures += 1
                except Exception as e:
                    self.stdout.write(f' - AI connector test skipped: {e}')
                    failures += 1
            else:
                self.stdout.write(' - AI module does not expose _safe_call; unable to test')
                failures += 1
        except Exception as e:
            self.stdout.write(f' - Could not import AI module: {e}')
            failures += 1

        # Rate limit sane defaults
        self.stdout.write('\nChecking rate limit settings:')
        rate_limit = getattr(settings, 'INTERVIEW_PRACTICE_RATE_LIMIT_PER_MINUTE', None)
        if rate_limit is None:
            self.stdout.write(' - INTERVIEW_PRACTICE_RATE_LIMIT_PER_MINUTE not set; recommend setting to 60 or lower')
        else:
            self.stdout.write(f' - INTERVIEW_PRACTICE_RATE_LIMIT_PER_MINUTE = {rate_limit}')
            if rate_limit > 1000:
                self.stdout.write('   -> Warning: very high rate limit')

        self.stdout.write('\nValidation complete.')
        if failures:
            self.stdout.write(f'Found {failures} potential issues. See output above.')
            sys.exit(2)
        else:
            self.stdout.write('All checks passed.')
