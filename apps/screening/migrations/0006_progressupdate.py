# Generated migration for ProgressUpdate model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('screening', '0006_merge_20260114_2355'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProgressUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('update_type', models.CharField(
                    choices=[
                        ('upload_started', 'Upload Started'),
                        ('screening_started', 'Screening Started'),
                        ('screening_progress', 'Screening Progress'),
                        ('result_analyzed', 'Result Analyzed'),
                        ('export_started', 'Export Started'),
                        ('export_completed', 'Export Completed'),
                        ('export_failed', 'Export Failed'),
                        ('pipeline_push_started', 'Pipeline Push Started'),
                        ('pipeline_push_completed', 'Pipeline Push Completed'),
                        ('error_occurred', 'Error Occurred'),
                    ],
                    max_length=50
                )),
                ('title', models.CharField(max_length=255)),
                ('message', models.TextField(blank=True, default='')),
                ('progress_percent', models.IntegerField(default=0)),
                ('current_item', models.IntegerField(blank=True, null=True)),
                ('total_items', models.IntegerField(blank=True, null=True)),
                ('status', models.CharField(
                    choices=[
                        ('running', 'Running'),
                        ('completed', 'Completed'),
                        ('failed', 'Failed'),
                        ('paused', 'Paused'),
                    ],
                    default='running',
                    max_length=20
                )),
                ('error_message', models.TextField(blank=True, default='')),
                ('metadata', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('result', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='progress_updates', to='screening.screeningresult')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress_updates', to='screening.screeningsession')),
            ],
            options={
                'verbose_name': 'Progress Update',
                'verbose_name_plural': 'Progress Updates',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['session', '-created_at'], name='screening_progress_session_idx'),
                    models.Index(fields=['update_type', '-created_at'], name='screening_progress_type_idx'),
                    models.Index(fields=['status', '-created_at'], name='screening_progress_status_idx'),
                ],
            },
        ),
    ]
