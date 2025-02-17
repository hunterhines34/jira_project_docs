from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0006_alter_jirainstance_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='jirainstance',
            name='instance_type',
            field=models.CharField(
                choices=[('cloud', 'Jira Cloud'), ('server', 'Jira Server/Data Center')],
                default='cloud',
                help_text='Select whether this is a Cloud or Server/Data Center instance',
                max_length=10
            ),
        ),
    ] 