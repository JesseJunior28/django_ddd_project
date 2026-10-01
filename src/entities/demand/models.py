from django.contrib.postgres.fields import ArrayField
from django.db import models

class Demand(models.Model):
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    repetition_type = models.CharField(max_length=16, null=True, blank=True)
    status = models.CharField(max_length=8, default='ACTIVE')
    industry = models.ForeignKey('industry.Industry', null=True, blank=True, on_delete=models.PROTECT, related_name='demands')
    department = models.ForeignKey('zone.Department', on_delete=models.PROTECT, related_name='demands')
    target_user_roles = ArrayField(models.CharField(max_length=32), default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = 'demand'

class DemandBranch(models.Model):
    demand = models.ForeignKey(Demand, on_delete=models.CASCADE, related_name='branches')
    branch = models.ForeignKey('branch.Branch', on_delete=models.PROTECT, related_name='demands')
    planogram = models.ForeignKey('planogram.Planogram', on_delete=models.PROTECT, related_name='demand_branches')
    last_execution_occurrences_sync_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = 'demand_branch'
        constraints = [models.UniqueConstraint(fields=('demand','branch','planogram'), name='demand_branch_unique')]


class ExecutionOccurrence(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING'
        EXPIRED = 'EXPIRED'
        DONE = 'DONE'

    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    due_date = models.DateTimeField()
    demand_branch = models.ForeignKey(DemandBranch, on_delete=models.CASCADE, related_name='execution_occurrences')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'execution_occurrence'


class Execution(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING'
        APPROVED = 'APPROVED'
        REJECTED = 'REJECTED'

    score = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    observation = models.TextField(null=True, blank=True)
    executed_by_user = models.ForeignKey('user.User', on_delete=models.PROTECT, related_name='executions')
    execution_occurrence = models.ForeignKey(ExecutionOccurrence, on_delete=models.PROTECT, related_name='executions')
    review = models.OneToOneField('review.ExecutionReview', null=True, blank=True, on_delete=models.SET_NULL, related_name='execution')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'execution'


class ExecutionDetail(models.Model):
    image_url = models.CharField(max_length=1024)
    sequence = models.IntegerField()
    layout_element = models.ForeignKey('branch_layout.LayoutElement', null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name='execution_details')
    execution = models.ForeignKey(Execution, on_delete=models.CASCADE, related_name='execution_details')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'execution_detail'


class ExecutionAudit(models.Model):
    current_stock = models.IntegerField()
    is_exposed = models.BooleanField(null=True, blank=True)
    is_position_acceptable = models.BooleanField(null=True, blank=True)
    non_exposition_reason = models.CharField(max_length=32, null=True, blank=True)
    execution = models.ForeignKey(Execution, null=True, blank=True, on_delete=models.CASCADE, related_name='audits')
    routine_execution = models.ForeignKey('routine.RoutineExecution', null=True, blank=True, on_delete=models.CASCADE, related_name='audits')
    product_exposition = models.ForeignKey('product.ProductExpositionDetail', null=True, blank=True,
                                           on_delete=models.SET_NULL, related_name='execution_audits')

    class Meta:
        db_table = 'execution_audit'
