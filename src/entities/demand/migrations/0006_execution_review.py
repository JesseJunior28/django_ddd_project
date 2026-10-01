import django.db.models.deletion
from django.db import migrations,models
class Migration(migrations.Migration):
 dependencies=[('demand','0005_executionaudit'),('review','0001_initial')]
 operations=[migrations.AddField(model_name='execution',name='review',field=models.OneToOneField(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='execution',to='review.executionreview'))]
