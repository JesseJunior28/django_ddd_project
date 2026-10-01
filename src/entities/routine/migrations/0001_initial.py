import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):
 initial=True
 dependencies=[('branch','0001_initial'),('branch_layout','0001_initial'),('planogram','0001_initial'),('user','0003_reset_token_unbounded')]
 operations=[
  migrations.CreateModel(name='RoutineDemand',fields=[
   ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('status',models.CharField(default='ACTIVE',max_length=8)),('created_at',models.DateTimeField(auto_now_add=True)),('updated_at',models.DateTimeField(auto_now=True)),
   ('branch',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='routine_demands',to='branch.branch')),('created_by_user',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='routine_demands',to='user.user')),('layout_element',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,to='branch_layout.layoutelement')),('module',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,to='planogram.module'))],options={'db_table':'routine_demand'}),
  migrations.CreateModel(name='RoutineExecution',fields=[
   ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('status',models.CharField(default='PENDING',max_length=8)),('score',models.FloatField(blank=True,null=True)),('observation',models.TextField(blank=True,null=True)),('old_module_image_url',models.CharField(max_length=1024)),('new_module_image_url',models.CharField(blank=True,max_length=1024,null=True)),('created_at',models.DateTimeField(auto_now_add=True)),('updated_at',models.DateTimeField(auto_now=True)),('executed_by_user',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='routine_executions',to='user.user')),('routine_demand',models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name='execution',to='routine.routinedemand'))],options={'db_table':'routine_execution'})]
