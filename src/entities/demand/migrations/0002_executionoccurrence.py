import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('demand', '0001_initial')]
    operations = [migrations.CreateModel(name='ExecutionOccurrence', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('status', models.CharField(choices=[('PENDING', 'Pending'), ('EXPIRED', 'Expired'), ('FINISHED', 'Finished')], default='PENDING', max_length=8)),
        ('due_date', models.DateTimeField()), ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
        ('demand_branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='execution_occurrences', to='demand.demandbranch')),
    ], options={'db_table': 'execution_occurrence'})]
