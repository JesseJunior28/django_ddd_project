import django.db.models.deletion
from django.db import migrations,models
class Migration(migrations.Migration):
 dependencies=[('demand','0006_execution_review'),('routine','0002_routineexecution_review')]
 operations=[migrations.AddField(model_name='executionaudit',name='routine_execution',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.CASCADE,related_name='audits',to='routine.routineexecution'))]
