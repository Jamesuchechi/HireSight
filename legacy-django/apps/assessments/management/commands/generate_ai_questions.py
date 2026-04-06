from django.core.management.base import BaseCommand
from apps.assessments.ai_utils import generate_questions_for_skill
from apps.assessments.models import QuestionPool


class Command(BaseCommand):
    help = 'Generate assessment questions using Mistral AI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skill',
            type=str,
            required=True,
            help='Skill name (e.g., Python, JavaScript, React)'
        )
        parser.add_argument(
            '--difficulty',
            type=str,
            default='INTERMEDIATE',
            choices=['BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT'],
            help='Difficulty level'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of questions to generate'
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            help='Auto-verify generated questions (skip admin review)'
        )

    def handle(self, *args, **options):
        skill = options['skill']
        difficulty = options['difficulty']
        count = options['count']
        auto_verify = options['verify']
        
        self.stdout.write(f'Generating {count} {difficulty} questions for {skill}...')
        
        try:
            questions = generate_questions_for_skill(skill, difficulty, count)
            
            if auto_verify:
                QuestionPool.objects.filter(
                    id__in=[q.id for q in questions]
                ).update(is_verified=True)
                self.stdout.write(self.style.SUCCESS(f'✓ Generated and verified {len(questions)} questions'))
            else:
                self.stdout.write(self.style.SUCCESS(f'✓ Generated {len(questions)} questions (pending review)'))
            
            # Show summary
            self.stdout.write('\nSummary:')
            for q in questions[:3]:  # Show first 3
                self.stdout.write(f'  • {q.question[:80]}...')
            
            if len(questions) > 3:
                self.stdout.write(f'  ... and {len(questions) - 3} more')
            
            self.stdout.write(f'\nReview questions at: /admin/assessments/questionpool/')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))