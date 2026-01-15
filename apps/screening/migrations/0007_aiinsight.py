# Generated migration for AI Insight models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('screening', '0006_progressupdate'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AIInsight',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('insight_type', models.CharField(
                    choices=[
                        ('interview_questions', 'Interview Questions'),
                        ('ai_notes', 'AI Notes'),
                        ('rejection_reasons', 'Rejection Reasons'),
                        ('resume_parsing', 'Resume Parsing'),
                    ],
                    help_text='Type of AI insight',
                    max_length=50
                )),
                ('title', models.CharField(help_text='Title of the insight', max_length=255)),
                ('content', models.JSONField(default=dict, help_text='Structured insight content (varies by type)')),
                ('summary', models.TextField(blank=True, default='', help_text='Plain text summary of the insight')),
                ('model_used', models.CharField(default='mistral-7b', help_text='Mistral model version used', max_length=50)),
                ('tokens_used', models.IntegerField(default=0, help_text='Number of tokens used for generation')),
                ('generation_time', models.FloatField(default=0.0, help_text='Time in seconds to generate insight')),
                ('confidence_score', models.FloatField(
                    default=0.0,
                    help_text='Confidence score (0-1) of the AI insight',
                    validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)]
                )),
                ('is_approved', models.BooleanField(default=False, help_text='Whether recruiter has approved this insight')),
                ('is_used', models.BooleanField(default=False, help_text='Whether this insight was actually used')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('result', models.OneToOneField(help_text='The screening result this insight is for', on_delete=django.db.models.deletion.CASCADE, related_name='ai_insight', to='screening.screeningresult')),
            ],
            options={
                'verbose_name': 'AI Insight',
                'verbose_name_plural': 'AI Insights',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='InsightFeedback',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('rating', models.CharField(
                    choices=[
                        ('helpful', 'Helpful'),
                        ('partially_helpful', 'Partially Helpful'),
                        ('not_helpful', 'Not Helpful'),
                        ('incorrect', 'Incorrect'),
                    ],
                    help_text='Rating of the insight',
                    max_length=20
                )),
                ('comment', models.TextField(blank=True, default='', help_text='Optional detailed feedback')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('insight', models.ForeignKey(help_text='The insight this feedback is for', on_delete=django.db.models.deletion.CASCADE, related_name='feedback', to='screening.aiinsight')),
                ('user', models.ForeignKey(help_text='User who provided feedback', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ai_insight_feedback', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Insight Feedback',
                'verbose_name_plural': 'Insight Feedback',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='aiinsight',
            index=models.Index(fields=['result', 'insight_type'], name='ai_insight_result_type_idx'),
        ),
        migrations.AddIndex(
            model_name='aiinsight',
            index=models.Index(fields=['insight_type', '-created_at'], name='ai_insight_type_date_idx'),
        ),
        migrations.AddIndex(
            model_name='aiinsight',
            index=models.Index(fields=['is_approved', '-created_at'], name='ai_insight_approved_idx'),
        ),
        migrations.AddIndex(
            model_name='insightfeedback',
            index=models.Index(fields=['insight', '-created_at'], name='insight_feedback_idx'),
        ),
        migrations.AddIndex(
            model_name='insightfeedback',
            index=models.Index(fields=['rating', '-created_at'], name='insight_rating_idx'),
        ),
    ]
