import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [('user', '0003_reset_token_unbounded')]
    operations = [migrations.CreateModel(name='Notification', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('message', models.TextField()), ('data', models.JSONField()),
        ('created_at', models.DateTimeField(auto_now_add=True)), ('viewed_at', models.DateTimeField(blank=True, null=True)),
        ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='user.user')),
    ], options={'db_table':'notification','ordering':['-created_at']})]
