"""
Management command to compile all translation files (.po to .mo)
Usage: python manage.py compile_all_translations
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pathlib import Path
import subprocess
import os


class Command(BaseCommand):
    help = 'Compile all translation files from .po to .mo format'

    def add_arguments(self, parser):
        parser.add_argument(
            '--use-fuzzy',
            action='store_true',
            dest='use_fuzzy',
            default=False,
            help='Include fuzzy translations in compiled files',
        )

    def handle(self, *args, **options):
        """Execute translation compilation"""
        locale_paths = settings.LOCALE_PATHS

        if not locale_paths:
            raise CommandError('LOCALE_PATHS is not configured in settings')

        compiled_count = 0
        error_count = 0

        for locale_path in locale_paths:
            locale_path = Path(locale_path)

            if not locale_path.exists():
                self.stdout.write(
                    self.style.WARNING(
                        f'Locale path does not exist: {locale_path}'
                    )
                )
                continue

            # Find all .po files
            po_files = list(locale_path.rglob('*.po'))

            if not po_files:
                self.stdout.write(
                    self.style.WARNING(
                        f'No .po files found in {locale_path}'
                    )
                )
                continue

            for po_file in po_files:
                mo_file = po_file.with_suffix('.mo')
                language_code = po_file.parent.parent.name

                try:
                    # Use msgfmt to compile
                    cmd = ['msgfmt', '-o', str(mo_file), str(po_file)]

                    if options['use_fuzzy']:
                        cmd.insert(1, '--use-fuzzy')

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=True
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Compiled: {language_code} '
                            f'({po_file.name} → {mo_file.name})'
                        )
                    )
                    compiled_count += 1

                except subprocess.CalledProcessError as e:
                    error_msg = e.stderr or str(e)
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Error compiling {language_code}: {error_msg}'
                        )
                    )
                    error_count += 1

                except FileNotFoundError:
                    self.stdout.write(
                        self.style.ERROR(
                            'msgfmt command not found. '
                            'Please install gettext tools: '
                            'apt-get install gettext (Debian/Ubuntu) or '
                            'brew install gettext (macOS)'
                        )
                    )
                    error_count += 1
                    break

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f'Translation compilation complete: '
                f'{compiled_count} compiled, {error_count} errors'
            )
        )

        if error_count > 0:
            raise CommandError(f'{error_count} compilation errors occurred')
