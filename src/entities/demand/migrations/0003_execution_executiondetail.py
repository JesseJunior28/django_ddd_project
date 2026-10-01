import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('branch_layout', '0001_initial'),
        ('demand', '0002_executionoccurrence'),
        ('user', '0003_reset_token_unbounded'),
    ]

    operations = [
        migrations.CreateModel(
            name='Execution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=8)),
                ('observation', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('executed_by_user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='executions', to='user.user')),
                ('execution_occurrence', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='executions', to='demand.executionoccurrence')),
            ],
            options={'db_table': 'execution'},
        ),
        migrations.CreateModel(
            name='ExecutionDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_url', models.CharField(max_length=1024)),
                ('sequence', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('execution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='execution_details', to='demand.execution')),
                ('layout_element', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='execution_details', to='branch_layout.layoutelement')),
            ],
            options={'db_table': 'execution_detail'},
        ),
    ]
