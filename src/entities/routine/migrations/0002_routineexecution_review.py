import django.db.models.deletion
from django.db import migrations,models
class Migration(migrations.Migration):
 dependencies=[('routine','0001_initial'),('review','0001_initial')]
 operations=[migrations.AddField(model_name='routineexecution',name='review',field=models.OneToOneField(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='routine_execution',to='review.executionreview'))]
