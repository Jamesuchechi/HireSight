# Generated migration file
# apps/jobs/migrations/0001_initial.py

import uuid
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(db_index=True, help_text='Job title', max_length=200)),
                ('slug', models.SlugField(db_index=True, help_text='URL-friendly job identifier', max_length=250, unique=True)),
                ('description', models.TextField(help_text='Detailed job description')),
                ('responsibilities', models.TextField(blank=True, help_text='Key responsibilities')),
                ('requirements', models.JSONField(blank=True, default=dict, help_text='Job requirements (skills, experience, education)')),
                ('nice_to_have', models.TextField(blank=True, help_text='Nice-to-have qualifications')),
                ('benefits', models.TextField(blank=True, help_text='Benefits and perks')),
                ('location', models.CharField(db_index=True, help_text='Job location (city, state, country)', max_length=200)),
                ('is_remote', models.BooleanField(default=False, help_text='Is this a remote position?')),
                ('remote_type', models.CharField(choices=[('onsite', 'On-site'), ('remote', 'Fully Remote'), ('hybrid', 'Hybrid')], default='onsite', help_text='Remote work type', max_length=20)),
                ('timezone_preference', models.CharField(blank=True, help_text='Preferred timezone (if remote)', max_length=100)),
                ('employment_type', models.CharField(choices=[('full_time', 'Full-time'), ('part_time', 'Part-time'), ('contract', 'Contract'), ('freelance', 'Freelance'), ('internship', 'Internship')], default='full_time', help_text='Type of employment', max_length=20)),
                ('experience_level', models.CharField(choices=[('entry', 'Entry Level'), ('mid', 'Mid Level'), ('senior', 'Senior Level'), ('lead', 'Lead/Principal'), ('executive', 'Executive')], default='mid', help_text='Required experience level', max_length=20)),
                ('salary_min', models.DecimalField(blank=True, decimal_places=2, help_text='Minimum salary', max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('salary_max', models.DecimalField(blank=True, decimal_places=2, help_text='Maximum salary', max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('salary_currency', models.CharField(default='USD', help_text='Currency code (e.g., USD, EUR)', max_length=3)),
                ('salary_period', models.CharField(choices=[('hourly', 'Per Hour'), ('monthly', 'Per Month'), ('yearly', 'Per Year')], default='yearly', help_text='Salary payment period', max_length=20)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('active', 'Active'), ('closed', 'Closed'), ('archived', 'Archived')], db_index=True, default='draft', help_text='Job posting status', max_length=20)),
                ('is_featured', models.BooleanField(db_index=True, default=False, help_text='Feature this job (premium)')),
                ('positions_available', models.PositiveIntegerField(default=1, help_text='Number of positions available', validators=[django.core.validators.MinValueValidator(1)])),
                ('application_deadline', models.DateTimeField(blank=True, help_text='Application deadline', null=True)),
                ('requires_cover_letter', models.BooleanField(default=False, help_text='Require cover letter?')),
                ('requires_portfolio', models.BooleanField(default=False, help_text='Require portfolio?')),
                ('screening_questions', models.JSONField(blank=True, default=list, help_text='Custom screening questions')),
                ('application_email', models.EmailField(blank=True, help_text='Email for applications (optional)', max_length=254)),
                ('views_count', models.PositiveIntegerField(default=0, help_text='Number of views')),
                ('applications_count', models.PositiveIntegerField(default=0, help_text='Number of applications')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('published_at', models.DateTimeField(blank=True, help_text='When job was published', null=True)),
                ('closed_at', models.DateTimeField(blank=True, help_text='When job was closed', null=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jobs', to='accounts.companyprofile')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SavedJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('saved_at', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True, help_text='Personal notes about this job')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_by', to='jobs.job')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_jobs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-saved_at'],
                'unique_together': {('user', 'job')},
            },
        ),
        migrations.CreateModel(
            name='JobView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('viewed_at', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=255)),
                ('referrer', models.CharField(blank=True, max_length=255)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='views', to='jobs.job')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_views', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-viewed_at'],
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['company', 'status'], name='jobs_job_company_status_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['status', '-published_at'], name='jobs_job_status_published_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['location', 'status'], name='jobs_job_location_status_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['employment_type', 'status'], name='jobs_job_employment_status_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['experience_level', 'status'], name='jobs_job_experience_status_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['is_featured', 'status'], name='jobs_job_featured_status_idx'),
        ),
        migrations.AddIndex(
            model_name='savedjob',
            index=models.Index(fields=['user', '-saved_at'], name='jobs_savedjob_user_saved_idx'),
        ),
        migrations.AddIndex(
            model_name='jobview',
            index=models.Index(fields=['job', '-viewed_at'], name='jobs_jobview_job_viewed_idx'),
        ),
        migrations.AddIndex(
            model_name='jobview',
            index=models.Index(fields=['user', '-viewed_at'], name='jobs_jobview_user_viewed_idx'),
        ),
        # Add constraints
        migrations.AddConstraint(
            model_name='job',
            constraint=models.CheckConstraint(
                name='salary_max_gte_min',
                condition=models.Q(salary_max__gte=models.F('salary_min')) | models.Q(salary_max__isnull=True)
            ),
        ),
    ]