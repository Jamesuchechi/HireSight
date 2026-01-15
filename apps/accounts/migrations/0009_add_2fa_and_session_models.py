# accounts/migrations/0007_add_2fa_and_session_models.py
# Generated migration file - create this in your migrations folder

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_add_email_change_token'),  
    ]

    operations = [
        # Add two_factor_enabled field to User model
        migrations.AddField(
            model_name='user',
            name='two_factor_enabled',
            field=models.BooleanField(default=False, help_text='Whether two-factor authentication is enabled'),
        ),
        
        # Create APIKey model
        migrations.CreateModel(
            name='APIKey',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Descriptive name for this API key', max_length=255)),
                ('key', models.CharField(help_text='The actual API key string', max_length=64, unique=True)),
                ('key_prefix', models.CharField(help_text='First 8 characters of the key for display purposes', max_length=8)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_used_at', models.DateTimeField(blank=True, help_text='Last time this key was used', null=True)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this key is currently active')),
                ('user', models.ForeignKey(help_text='User who owns this API key', on_delete=django.db.models.deletion.CASCADE, related_name='api_keys', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'API Key',
                'verbose_name_plural': 'API Keys',
                'db_table': 'api_keys',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create ProfileView model
        migrations.CreateModel(
            name='ProfileView',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('viewer_ip', models.GenericIPAddressField(blank=True, help_text='IP address of anonymous viewers', null=True)),
                ('viewer_user_agent', models.TextField(blank=True, help_text='Browser/device information')),
                ('viewed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('profile_user', models.ForeignKey(help_text='User whose profile was viewed', on_delete=django.db.models.deletion.CASCADE, related_name='profile_views_received', to=settings.AUTH_USER_MODEL)),
                ('viewer', models.ForeignKey(blank=True, help_text='User who viewed the profile (null if anonymous)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='profile_views_made', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Profile View',
                'verbose_name_plural': 'Profile Views',
                'db_table': 'profile_views',
                'ordering': ['-viewed_at'],
            },
        ),
        
        # Create UserSession model
        migrations.CreateModel(
            name='UserSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('session_key', models.CharField(help_text='Django session key', max_length=40, unique=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address of the session', null=True)),
                ('user_agent', models.TextField(blank=True, help_text='Browser/device information')),
                ('location', models.CharField(blank=True, help_text='Approximate location (city, country)', max_length=255)),
                ('device_type', models.CharField(blank=True, help_text='Device type (desktop, mobile, tablet)', max_length=50)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_activity', models.DateTimeField(default=django.utils.timezone.now)),
                ('expires_at', models.DateTimeField(help_text='When this session expires')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Session',
                'verbose_name_plural': 'User Sessions',
                'db_table': 'user_sessions',
                'ordering': ['-last_activity'],
            },
        ),
        
        # Create AccountDeletionLog model
        migrations.CreateModel(
            name='AccountDeletionLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('user_email', models.EmailField(help_text='Email of deleted account', max_length=254)),
                ('account_type', models.CharField(help_text='Account type (personal/company)', max_length=20)),
                ('deletion_reason', models.TextField(blank=True, help_text='Optional reason for deletion')),
                ('deleted_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('deleted_by_user', models.BooleanField(default=True, help_text='True if user deleted their own account')),
                ('account_age_days', models.IntegerField(blank=True, help_text='How many days the account existed', null=True)),
                ('total_applications', models.IntegerField(default=0, help_text='Number of applications made (if personal)')),
                ('total_job_posts', models.IntegerField(default=0, help_text='Number of jobs posted (if company)')),
            ],
            options={
                'verbose_name': 'Account Deletion Log',
                'verbose_name_plural': 'Account Deletion Logs',
                'db_table': 'account_deletion_logs',
                'ordering': ['-deleted_at'],
            },
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='apikey',
            index=models.Index(fields=['user', 'is_active'], name='api_keys_user_id_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='apikey',
            index=models.Index(fields=['key'], name='api_keys_key_idx'),
        ),
        migrations.AddIndex(
            model_name='profileview',
            index=models.Index(fields=['profile_user', '-viewed_at'], name='profile_views_profile_user_idx'),
        ),
        migrations.AddIndex(
            model_name='profileview',
            index=models.Index(fields=['viewer', '-viewed_at'], name='profile_views_viewer_idx'),
        ),
        migrations.AddIndex(
            model_name='usersession',
            index=models.Index(fields=['user', '-last_activity'], name='user_sessions_user_activity_idx'),
        ),
        migrations.AddIndex(
            model_name='usersession',
            index=models.Index(fields=['session_key'], name='user_sessions_key_idx'),
        ),
        migrations.AddIndex(
            model_name='accountdeletionlog',
            index=models.Index(fields=['deleted_at'], name='deletion_logs_date_idx'),
        ),
        migrations.AddIndex(
            model_name='accountdeletionlog',
            index=models.Index(fields=['account_type'], name='deletion_logs_type_idx'),
        ),
    ]