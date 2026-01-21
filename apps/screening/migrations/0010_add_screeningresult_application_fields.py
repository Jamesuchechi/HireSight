from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('screening', '0009_alter_aiinsight_result_field'),
        ('applications', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='screeningresult',
            name='application',
            field=models.ForeignKey(
                blank=True,
                help_text='Application being screened',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='screening_results',
                to='applications.application'
            ),
        ),
        migrations.AddField(
            model_name='screeningresult',
            name='screening_answers',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Candidate's answers to job screening questions"
            ),
        ),
        migrations.AddField(
            model_name='screeningresult',
            name='assessment_data',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Skill assessment results and scores"
            ),
        ),
    ]
