from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('demand', '0003_execution_executiondetail')]

    operations = [
        migrations.AlterField(
            model_name='executionoccurrence',
            name='status',
            field=models.CharField(
                choices=[('PENDING', 'Pending'), ('EXPIRED', 'Expired'), ('DONE', 'Done')],
                default='PENDING', max_length=8,
            ),
        ),
    ]
