from django.db import models
class RoutineDemand(models.Model):
 status=models.CharField(max_length=8,default='ACTIVE')
 created_by_user=models.ForeignKey('user.User',on_delete=models.PROTECT,related_name='routine_demands')
 branch=models.ForeignKey('branch.Branch',on_delete=models.PROTECT,related_name='routine_demands')
 module=models.ForeignKey('planogram.Module',null=True,blank=True,on_delete=models.SET_NULL)
 layout_element=models.ForeignKey('branch_layout.LayoutElement',null=True,blank=True,on_delete=models.SET_NULL)
 created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
 class Meta: db_table='routine_demand'
class RoutineExecution(models.Model):
 status=models.CharField(max_length=8,default='PENDING'); score=models.FloatField(null=True,blank=True); observation=models.TextField(null=True,blank=True)
 old_module_image_url=models.CharField(max_length=1024); new_module_image_url=models.CharField(max_length=1024,null=True,blank=True)
 executed_by_user=models.ForeignKey('user.User',on_delete=models.PROTECT,related_name='routine_executions')
 routine_demand=models.OneToOneField(RoutineDemand,on_delete=models.CASCADE,related_name='execution')
 review=models.OneToOneField('review.ExecutionReview',null=True,blank=True,on_delete=models.SET_NULL,related_name='routine_execution')
 created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
 class Meta: db_table='routine_execution'
