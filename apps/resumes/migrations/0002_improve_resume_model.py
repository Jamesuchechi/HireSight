
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('resumes', '0001_initial'),
    ]

    operations = [
        # Add new fields
        migrations.AddField(
            model_name='resume',
            name='parse_attempts',
            field=models.PositiveIntegerField(default=0, help_text='Number of parsing attempts'),
        ),
        migrations.AddField(
            model_name='resume',
            name='last_parse_attempt',
            field=models.DateTimeField(blank=True, help_text='Last time parsing was attempted', null=True),
        ),
        
        # Remove unique_together constraint if it exists
        migrations.AlterUniqueTogether(
            name='resume',
            unique_together=set(),
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='resume',
            index=models.Index(fields=['user', '-uploaded_at'], name='resumes_res_user_id_upload_idx'),
        ),
        migrations.AddIndex(
            model_name='resume',
            index=models.Index(fields=['user', 'is_primary'], name='resumes_res_user_id_primar_idx'),
        ),
        migrations.AddIndex(
            model_name='resume',
            index=models.Index(fields=['status', '-uploaded_at'], name='resumes_res_status_upload_idx'),
        ),
        migrations.AddIndex(
            model_name='resume',
            index=models.Index(fields=['status'], name='resumes_res_status_idx'),
        ),
        migrations.AddIndex(
            model_name='resume',
            index=models.Index(fields=['is_primary'], name='resumes_res_primary_idx'),
        ),
        migrations.AddIndex(
            model_name='resume',
            index=models.Index(fields=['uploaded_at'], name='resumes_res_upload_idx'),
        ),
        
        # Add check constraint for file size
        migrations.AddConstraint(
            model_name='resume',
            constraint=models.CheckConstraint(
                condition=models.Q(file_size__lte=5242880),
                name='file_size_limit'
            ),
        ),
    ]