# Auto-generated migration for PipelineIntegration model

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('screening', '0001_initial'),  # Update this to match your last migration
    ]

    operations = [
        migrations.CreateModel(
            name='PipelineIntegration',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('pushed', 'Pushed to Pipeline'), ('rejected', 'Rejected from Pipeline'), ('hired', 'Hired'), ('withdrawn', 'Withdrawn')], db_index=True, default='pending', help_text='Current pipeline status', max_length=20)),
                ('pushed_at', models.DateTimeField(auto_now_add=True, help_text='When candidate was pushed to pipeline')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Last update timestamp')),
                ('pipeline_id', models.CharField(blank=True, help_text='External pipeline system ID (if applicable)', max_length=100)),
                ('pipeline_url', models.URLField(blank=True, help_text='Link to candidate in pipeline system')),
                ('pipeline_stage', models.CharField(blank=True, help_text='Current stage in hiring pipeline', max_length=100)),
                ('stage_updated_at', models.DateTimeField(blank=True, help_text='When stage was last updated', null=True)),
                ('notes', models.TextField(blank=True, help_text='Notes about pipeline integration')),
                ('last_synced', models.DateTimeField(blank=True, help_text='Last time data was synced with pipeline', null=True)),
                ('sync_failed', models.BooleanField(default=False, help_text='Has sync with pipeline failed?')),
                ('sync_error', models.TextField(blank=True, help_text='Sync error details if failed')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pipeline_integrations', to='accounts.companyprofile')),
                ('job', models.ForeignKey(help_text='Job being applied for', null=True, on_delete=django.db.models.deletion.SET_NULL, to='jobs.job')),
                ('result', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='pipeline_integration', to='screening.screeningresult')),
            ],
            options={
                'verbose_name_plural': 'Pipeline Integrations',
                'ordering': ['-pushed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='pipelineintegration',
            index=models.Index(fields=['job', 'status'], name='screening_p_job_id_status_idx'),
        ),
        migrations.AddIndex(
            model_name='pipelineintegration',
            index=models.Index(fields=['company', '-pushed_at'], name='screening_p_company_pushed_idx'),
        ),
        migrations.AddIndex(
            model_name='pipelineintegration',
            index=models.Index(fields=['status', '-pushed_at'], name='screening_p_status_pushed_idx'),
        ),
    ]
