from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interviews', '0002_alter_interview_options_remove_interview_timezone_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interview',
            name='timezone_name',
            field=models.CharField(
                max_length=50,
                default='UTC',
                help_text='Timezone for the scheduled date (e.g., America/New_York)',
                db_column='timezone',
            ),
        ),
    ]
