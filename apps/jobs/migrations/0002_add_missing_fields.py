from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Add missing fields to Job model:
    - department: Department or team for this position
    - education_required: Minimum education requirement
    - tags: Skills, keywords, and tags for this job
    """

    dependencies = [
        ('jobs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='department',
            field=models.CharField(
                blank=True, 
                help_text='Department or team for this position',
                max_length=100
            ),
        ),
        migrations.AddField(
            model_name='job',
            name='education_required',
            field=models.CharField(
                blank=True,
                help_text='Minimum education requirement',
                max_length=100
            ),
        ),
        migrations.AddField(
            model_name='job',
            name='tags',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Skills, keywords, and tags for this job'
            ),
        ),
    ]