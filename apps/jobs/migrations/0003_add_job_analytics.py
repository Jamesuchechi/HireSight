from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Add JobAnalytics model for comprehensive job performance tracking.
    """

    dependencies = [
        ('jobs', '0002_add_missing_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobAnalytics',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_views', models.PositiveIntegerField(default=0)),
                ('unique_views', models.PositiveIntegerField(default=0)),
                ('views_last_7_days', models.PositiveIntegerField(default=0)),
                ('views_last_30_days', models.PositiveIntegerField(default=0)),
                ('total_applications', models.PositiveIntegerField(default=0)),
                ('applications_last_7_days', models.PositiveIntegerField(default=0)),
                ('applications_last_30_days', models.PositiveIntegerField(default=0)),
                ('application_rate', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('interview_rate', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('offer_rate', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('hire_rate', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('avg_time_to_first_application', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('avg_time_to_interview', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('avg_time_to_offer', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('avg_time_to_hire', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('applications_by_source', models.JSONField(blank=True, default=dict)),
                ('applicant_locations', models.JSONField(blank=True, default=dict)),
                ('experience_levels', models.JSONField(blank=True, default=dict)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('job', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='analytics', to='jobs.job')),
            ],
            options={
                'verbose_name_plural': 'Job Analytics',
            },
        ),
    ]