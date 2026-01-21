from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('screening', '0008_add_file_path_to_screening_result'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aiinsight',
            name='result',
            field=models.ForeignKey(
                help_text='The screening result this insight is for',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='ai_insights',
                to='screening.screeningresult'
            ),
        ),
    ]
