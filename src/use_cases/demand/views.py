from datetime import datetime
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from src.middlewares.auth import AuthenticatedController
from src.entities.demand.models import Demand, DemandBranch, ExecutionOccurrence, Execution, ExecutionDetail, ExecutionAudit
from src.entities.branch_layout.models import LayoutElement
from src.entities.product.models import ProductExpositionDetail, BranchProductStock
from src.services.storage.local import LocalProductStorage
from src.entities.notification.models import Notification
from src.entities.routine.models import RoutineDemand, RoutineExecution
from src.entities.review.models import ReviewQuestion, ReviewAnswer, ExecutionReview, ReviewQuestionAnswer
from src.entities.industry.models import Industry
from src.entities.zone.models import Department
from src.entities.branch.models import Branch
from src.entities.branch_layout.models import ElementModuleConfiguration

def entity(d):
    dep=d.department
    iso=lambda value:value.isoformat(timespec='milliseconds').replace('+00:00','Z') if value else None
    return {'id':d.id,'title':d.title,**({'description':d.description} if d.description else {}),'startDate':iso(d.start_date),'endDate':iso(d.end_date),
      **({'repetitionType':d.repetition_type} if d.repetition_type else {}),'status':d.status,'targetUserRoles':d.target_user_roles,'createdAt':d.created_at,'updatedAt':d.updated_at,
      **({'industryId':d.industry_id} if d.industry_id else {}),'departmentId':d.department_id,
      'department':{'id':dep.id,'name':dep.name,'orientation':dep.orientation,'zoneId':dep.zone_id},
      'branches':[{'id':x.id,'demandId':x.demand_id,'branchId':x.branch_id,'planogramId':x.planogram_id,**({'lastExecutionOccurrencesSyncAt':x.last_execution_occurrences_sync_at} if x.last_execution_occurrences_sync_at else {}),'branch':{'id':x.branch.id,'name':x.branch.name,'city':x.branch.city,'address':x.branch.address,'uf':x.branch.uf,'createdAt':x.branch.created_at,'updatedAt':x.branch.updated_at}} for x in d.branches.select_related('branch').all()]}

class DemandBase(AuthenticatedController): authorized_roles=('ADMIN',)
class DemandView(DemandBase):
 def post(self,request):
  data=request.data
  try:
   if not isinstance(data,dict) or not isinstance(data.get('title'),str) or not isinstance(data.get('departmentId'),int) or not isinstance(data.get('planogramIds'),list) or not data['planogramIds']: raise ValueError()
   start=datetime.fromisoformat(data['startDate'].replace('Z','+00:00')); end=datetime.fromisoformat(data['endDate'].replace('Z','+00:00')) if data.get('endDate') else None
   if (not end and not data.get('repetitionType')) or (end and end<=start): raise ValueError()
  except (ValueError,TypeError,KeyError): return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})
  if not Department.objects.filter(pk=data['departmentId']).exists(): return self.not_found({'name':'DepartmentNotFoundError','message':f"Departamento com ID {data['departmentId']} não foi encontrado."})
  if data.get('industryId') and not Industry.objects.filter(pk=data['industryId']).exists(): return self.not_found({'name':'IndustryNotFoundError','message':f"Indústria com ID {data['industryId']} não foi encontrada."})
  configs=ElementModuleConfiguration.objects.filter(module__planogram_id__in=data['planogramIds']).select_related('layout_element__branch_layout','module')
  pairs=[(c.layout_element.branch_layout.branch_id,c.module.planogram_id) for c in configs if not data.get('branchesIds') or c.layout_element.branch_layout.branch_id in data['branchesIds']]
  if not pairs:return self.not_found({'name':'PlanogramsBranchesNotFoundError','message':'Não foi encontrada nenhuma loja para os planogramas selecionados na demanda'})
  with transaction.atomic():
   demand=Demand.objects.create(title=data['title'],description=data.get('description'),start_date=start,end_date=end,repetition_type=data.get('repetitionType'),department_id=data['departmentId'],industry_id=data.get('industryId'),target_user_roles=data.get('targetUserRoles') or [])
   DemandBranch.objects.bulk_create([DemandBranch(demand=demand,branch_id=b,planogram_id=p) for b,p in dict.fromkeys(pairs)])
  return self.created(entity(Demand.objects.select_related('department__zone').get(pk=demand.pk)))
 def get(self,request):
  q=Demand.objects.select_related('department__zone').prefetch_related('branches__branch')
  if request.query_params.get('status') in ('ACTIVE','INACTIVE'):q=q.filter(status=request.query_params['status'])
  text=request.query_params.get('queryString'); q=q.filter(Q(title__icontains=text)|Q(department__name__icontains=text)) if text else q
  try: size=int(request.query_params.get('pageSize',10)); page=int(request.query_params.get('pageNumber',1))
  except ValueError:return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})
  total=q.count(); return self.ok({'totalPages':-(-total//size),'results':[entity(x) for x in q.order_by('status','-created_at')[(page-1)*size:page*size]]})
class DemandStatusView(DemandBase):
 def patch(self,request,id):
  if not isinstance(request.data,dict) or not isinstance(request.data.get('status'),bool):return self.bad_request({'name':'InputValidationError','message':'Tipo de status inválido para demanda'})
  d=Demand.objects.filter(pk=int(id)).first()
  if not d:return self.internal_server_error({'name':'DemandNotFoundError','message':f'Demanda com ID {id} não foi encontrada.'})
  d.status='ACTIVE' if request.data['status'] else 'INACTIVE';d.save();return self.ok(entity(Demand.objects.select_related('department__zone').get(pk=d.pk)))

class ExecutionOccurrenceView(AuthenticatedController):
 authorized_roles=('LAYOUT','BRANCH')
 def get(self,request,branch_id):
  if not branch_id.isdigit():return self.bad_request({'name':'InputValidationError','message':'Tipo inválido para id da filial'})
  rows=ExecutionOccurrence.objects.filter(status='PENDING',demand_branch__branch_id=int(branch_id),demand_branch__demand__status='ACTIVE').select_related('demand_branch__planogram').order_by('due_date')
  return self.ok({'results':[{'executionOccurrenceId':x.id,'status':x.status,'dueDate':x.due_date.isoformat(timespec='milliseconds').replace('+00:00','Z'),'planogramId':x.demand_branch.planogram_id,'layoutElementIds':list(ElementModuleConfiguration.objects.filter(module__planogram_id=x.demand_branch.planogram_id,layout_element__branch_layout__branch_id=int(branch_id)).values_list('layout_element_id',flat=True))} for x in rows]})


class CreateBranchExecutionView(AuthenticatedController):
 authorized_roles=('BRANCH','LAYOUT')

 def post(self, request):
  files=request.FILES.getlist('images')
  raw_occurrence=request.data.get('executionOccurrenceId')
  try:
   occurrence_id=int(raw_occurrence)
   user_id=int(request.token_claims.get('sub'))
   raw_elements=request.data.getlist('layoutElementsIds') if hasattr(request.data, 'getlist') else request.data.get('layoutElementsIds')
   if not isinstance(raw_elements, list): raw_elements=[raw_elements]
   if len(files) == 1 and len(raw_elements) == 1: element_ids=[int(raw_elements[0])]
   elif len(files) == len(raw_elements): element_ids=[int(item) for item in raw_elements]
   else: raise ValueError()
   if not files: raise ValueError()
  except (TypeError, ValueError):
   return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})

  saved=[]
  try:
   with transaction.atomic():
    occurrence=ExecutionOccurrence.objects.select_for_update().filter(pk=occurrence_id).first()
    if not occurrence:
     return self.not_found({'name':'ExecutionOccurrenceNotFoundError','message':f'Ocorrência de execução com ID {occurrence_id} não foi encontrada.'})
    if occurrence.status != 'PENDING':
     return self.conflict({'name':'ExecutionOccurrenceStatusConflict','message':f'Ocorrência de execução com ID {occurrence_id} não está aberta.'})
    if timezone.now() > occurrence.due_date:
     return self.conflict({'name':'ExecutionDueDateConflict','message':'A ocorrência dessa demanda está expirada.'})
    if Execution.objects.filter(execution_occurrence=occurrence, status__in=('PENDING','APPROVED')).exists():
     return self.conflict({'name':'ExecutionStatusConflict','message':'A execução para essa demanda já foi realizada anteriormente.'})
    elements=list(LayoutElement.objects.filter(pk__in=element_ids))
    if len(elements) != len(set(element_ids)):
     missing=next(item for item in element_ids if item not in {element.id for element in elements})
     return self.not_found({'name':'LayoutElementNotFound','message':f'Elemento de layout com ID {missing} não foi encontrado.'})
    storage=LocalProductStorage(directory='/tmp/django-execution-uploads')
    for image in files: saved.append(storage.save(image))
    execution=Execution.objects.create(execution_occurrence=occurrence,executed_by_user_id=user_id,observation=request.data.get('observation') or None)
    by_id={element.id:element for element in elements}
    ExecutionDetail.objects.bulk_create([ExecutionDetail(execution=execution,image_url=url,sequence=index + 1,layout_element=by_id[element_ids[index]]) for index,url in enumerate(saved)])
    planogram_id=occurrence.demand_branch.planogram_id
    branch_id=occurrence.demand_branch.branch_id
    expositions=ProductExpositionDetail.objects.filter(level__department_id=occurrence.demand_branch.planogram.department_id).select_related('product')
    stocks={(x.sku,x.ean):x.stock for x in BranchProductStock.objects.filter(branch_id=branch_id)}
    ExecutionAudit.objects.bulk_create([ExecutionAudit(execution=execution,product_exposition=item,current_stock=stocks.get((item.product.sku,item.product.ean),0),non_exposition_reason='UNSUFICIENT_STOCK' if stocks.get((item.product.sku,item.product.ean),0)<item.min_stock else None) for item in expositions])
    occurrence.status='DONE'; occurrence.save(update_fields=['status','updated_at'])
   return self.created()
  except ValueError as error:
   for name in saved: LocalProductStorage(directory='/tmp/django-execution-uploads').delete(name)
   return self.bad_request({'name':'InputValidationError','message':str(error)})
  except Exception:
   for name in saved: LocalProductStorage(directory='/tmp/django-execution-uploads').delete(name)
   raise


def _iso(value):
 return value.isoformat(timespec='milliseconds').replace('+00:00','Z') if value else None


class ExecutionDetailsView(AuthenticatedController):
 authorized_roles=('ADMIN','LAYOUT','REGIONAL_SUPERVISOR','BRANCH')

 def get(self, request, execution_id):
  if not execution_id.isdigit(): return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})
  execution=Execution.objects.select_related('execution_occurrence__demand_branch__demand__department','execution_occurrence__demand_branch__branch','executed_by_user').filter(pk=int(execution_id)).first()
  if not execution: return self.not_found({'name':'ExecutionNotFoundError','message':f'A execução com id {execution_id} não foi encontrada.'})
  occurrence=execution.execution_occurrence; link=occurrence.demand_branch; demand=link.demand
  details=[]
  for detail in execution.execution_details.select_related('layout_element__module_configuration__module__planogram__department__zone').order_by('id'):
   data={'id':detail.id,'executionId':execution.id,'imageUrl':detail.image_url,'sequence':detail.sequence,'createdAt':_iso(detail.created_at),'updatedAt':_iso(detail.updated_at)}
   if detail.layout_element_id:
    data['layoutElementId']=detail.layout_element_id
    config=getattr(detail.layout_element,'module_configuration',None)
    if config and config.module_id:
     planogram=config.module.planogram; department=planogram.department; zone=department.zone
     data['moduleConfiguration']={'layoutElementId':config.layout_element_id,'isMarketingPoint':config.is_marketing_point,'moduleId':config.module_id,'moduleDetails':{'planogramId':planogram.id,'planogramName':planogram.name,'moduleSequence':config.module.sequence,'zone':{'id':zone.id,'name':zone.name,'hexColor':zone.hex_color,'isMarketingZone':zone.is_marketing_zone,'department':{'id':department.id,'name':department.name}}}}
   details.append(data)
  grouped={}
  audits=execution.audits.select_related('product_exposition__product','product_exposition__level').order_by('id')
  for audit in audits:
   exposition=audit.product_exposition
   if not exposition: continue
   level=exposition.level
   row={'id':audit.id,'currentStock':audit.current_stock,'executionId':execution.id}
   if audit.is_exposed is not None: row['isExposed']=audit.is_exposed
   if audit.is_position_acceptable is not None: row['isPositionAcceptable']=audit.is_position_acceptable
   if audit.non_exposition_reason: row['nonExpositionReason']=audit.non_exposition_reason
   row['productExpositionId']=exposition.id
   row['productExposition']={'id':exposition.id,'productId':exposition.product_id,'levelId':exposition.level_id,'ranking':exposition.ranking,'priority':exposition.priority,'forefront':exposition.forefront,'minStock':exposition.min_stock,'fixedSide':exposition.fixed_side,'isExtraExposition':exposition.is_extra_exposition,'product':{'id':exposition.product.id,'sku':exposition.product.sku,'ean':exposition.product.ean,'name':exposition.product.name}}
   grouped.setdefault(level.id,{'levelId':level.id,'levelName':level.name,'audits':[]})['audits'].append(row)
  user=execution.executed_by_user
  return self.ok({'id':execution.id,'status':execution.status,'createdAt':_iso(execution.created_at),'updatedAt':_iso(execution.updated_at),'demand':{'id':demand.id,'title':demand.title},'branch':{'id':link.branch.id,'name':link.branch.name},'department':{'id':demand.department.id,'name':demand.department.name},'executionsDetails':details,'executedByUser':{'id':user.id,'email':user.email,'name':user.name,'role':user.role,'isActive':user.is_active,'createdAt':_iso(user.created_at),'updatedAt':_iso(user.updated_at)},'auditGroupedByLevel':list(grouped.values())})


class ListExecutionsView(AuthenticatedController):
 authorized_roles=('ADMIN','LAYOUT','REGIONAL_SUPERVISOR','BRANCH')

 def get(self, request):
  try:
   branch_id=request.query_params.get('branchId'); demand_id=request.query_params.get('demandId')
   if not branch_id and not demand_id: raise ValueError()
   branch_id=int(branch_id) if branch_id else None; demand_id=int(demand_id) if demand_id else None
   page=int(request.query_params.get('pageNumber',1)); size=int(request.query_params.get('pageSize',10))
   if page < 1 or size < 1: raise ValueError()
  except ValueError: return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})
  rows=Execution.objects.select_related('execution_occurrence__demand_branch__demand__department','execution_occurrence__demand_branch__branch').order_by('execution_occurrence_id')
  if branch_id: rows=rows.filter(execution_occurrence__demand_branch__branch_id=branch_id)
  if demand_id: rows=rows.filter(execution_occurrence__demand_branch__demand_id=demand_id)
  status_value=request.query_params.get('status')
  if status_value in ('PENDING','APPROVED','REJECTED'): rows=rows.filter(status=status_value)
  department=request.query_params.get('departmentName')
  if department: rows=rows.filter(execution_occurrence__demand_branch__demand__department__name__icontains=department)
  total=rows.count(); offset=(page-1)*size
  results=[]
  for item in rows[offset:offset+size]:
   link=item.execution_occurrence.demand_branch; demand=link.demand
   value={'id':item.id,'status':item.status,'createdAt':_iso(item.created_at),'updatedAt':_iso(item.updated_at),'demand':{'id':demand.id,'title':demand.title},'branch':{'id':link.branch.id,'name':link.branch.name},'department':{'id':demand.department.id,'name':demand.department.name}}
   if item.score is not None:value['score']=item.score
   if item.observation:value['observation']=item.observation
   results.append(value)
  return self.ok({'totalPages':-(-total//size),'results':results})


class UpdateExecutionStatusView(AuthenticatedController):
 authorized_roles=('ADMIN',)

 def patch(self, request):
  data=request.data
  if not isinstance(data,dict) or type(data.get('executionId')) is not int or data.get('status') not in ('APPROVED','REJECTED'):
   return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})
  execution=Execution.objects.filter(pk=data['executionId']).first()
  if not execution:
   return self.not_found({'name':'ExecutionNotFoundError','message':f"A execução com id {data['executionId']} não foi encontrada."})
  if execution.status != 'PENDING':
   return self.conflict({'name':'ExecutionStatusUpdateConflict','message':f'Não é possível aprovar/rejeitar a execução. Status atual é {execution.status}.'})
  return self.conflict({'name':'ExecutionWithoutReviewConflict','message':'Essa execução ainda não possui nota e não pode ser aprovada/rejeitada.'})


class EditExecutionAuditView(AuthenticatedController):
 authorized_roles=('ADMIN',)

 def post(self, request):
  data=request.data
  if not isinstance(data,dict) or type(data.get('executionId')) is not int or data.get('demandType') != 'ADMIN' or not isinstance(data.get('editedAudits'),list) or not data['editedAudits']:
   return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})
  execution=Execution.objects.filter(pk=data['executionId']).first()
  if not execution: return self.not_found({'name':'ExecutionNotFoundError','message':f"A execução com id {data['executionId']} não foi encontrada."})
  if execution.status != 'PENDING': return self.conflict({'name':'EditExecutionAuditStatusConflict','message':f'Não é possível editar auditorias. Status atual é {execution.status}.'})
  try:
   for change in data['editedAudits']:
    if not isinstance(change,dict) or type(change.get('executionAuditId')) is not int or any(type(change[key]) is not bool for key in ('isExposed','isPositionAcceptable') if key in change): raise ValueError()
    updates={}
    if 'isExposed' in change: updates['is_exposed']=change['isExposed']
    if 'isPositionAcceptable' in change: updates['is_position_acceptable']=change['isPositionAcceptable']
    ExecutionAudit.objects.filter(pk=change['executionAuditId'],execution=execution).update(**updates)
  except ValueError: return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})
  return self.ok()


class NotificationView(AuthenticatedController):
 def get(self, request):
  user_id=request.token_claims.get('sub')
  rows=Notification.objects.filter(user_id=user_id)
  return self.ok({'results':[{'id':item.id,'userId':item.user_id,'message':item.message,'data':item.data,'createdAt':_iso(item.created_at),**({'viewedAt':_iso(item.viewed_at)} if item.viewed_at else {})} for item in rows]})


class NotificationViewedView(AuthenticatedController):
 def patch(self, request, notification_id):
  if not notification_id.isdigit(): return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})
  Notification.objects.filter(pk=int(notification_id),user_id=request.token_claims.get('sub')).update(viewed_at=timezone.now())
  return self.ok()


class CreateRoutineDemandView(AuthenticatedController):
 authorized_roles=('ADMIN','LAYOUT')
 def post(self,request):
  try:
   branch_id=int(request.data.get('branchId')); element_id=int(request.data.get('layoutElementId')); user_id=int(request.token_claims['sub']); image=request.FILES['oldModuleImageUrl']
  except (KeyError,TypeError,ValueError): return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})
  element=LayoutElement.objects.select_related('module_configuration__module').filter(pk=element_id).first()
  if not element or not getattr(element,'module_configuration',None): return self.not_found({'name':'ElementModuleConfigurationNotFound','message':f'Configuração do elemento {element_id} não encontrada.'})
  if not element.module_configuration.module_id: return self.conflict({'name':'CreateRoutineDemandModuleConflict','message':'O elemento não possui módulo associado.'})
  if RoutineDemand.objects.filter(status='ACTIVE',layout_element_id=element_id,created_by_user_id=user_id).exists(): return self.conflict({'name':'RoutineDemandActiveConflict','message':'Já existe uma demanda de rotina ativa para este elemento.'})
  try: name=LocalProductStorage(directory='/tmp/django-routine-uploads').save(image)
  except ValueError as error:return self.bad_request({'name':'InputValidationError','message':str(error)})
  try:
   with transaction.atomic():
    demand=RoutineDemand.objects.create(branch_id=branch_id,layout_element=element,module_id=element.module_configuration.module_id,created_by_user_id=user_id)
    execution=RoutineExecution.objects.create(routine_demand=demand,executed_by_user_id=user_id,old_module_image_url=name)
   return self.created({'id':demand.id,'status':demand.status,'createdByUserId':user_id,'branchId':branch_id,'moduleId':demand.module_id,'layoutElementId':element_id,'createdAt':_iso(demand.created_at),'updatedAt':_iso(demand.updated_at),'execution':{'id':execution.id,'status':execution.status,'oldModuleImageUrl':name,'executedByUserId':user_id,'routineDemandId':demand.id,'createdAt':_iso(execution.created_at),'updatedAt':_iso(execution.updated_at)}})
  except Exception:
   LocalProductStorage(directory='/tmp/django-routine-uploads').delete(name); raise


class FinishRoutineExecutionView(AuthenticatedController):
 authorized_roles=('ADMIN','LAYOUT')
 def patch(self,request):
  try: demand_id=int(request.data.get('routineDemandId')); image=request.FILES['newModuleImageUrl']
  except (KeyError,TypeError,ValueError): return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})
  demand=RoutineDemand.objects.select_related('execution').filter(pk=demand_id).first()
  if not demand:return self.not_found({'name':'RoutineDemandNotFound','message':f'A demanda de rotina com id {demand_id} não foi encontrada.'})
  if demand.status!='ACTIVE':return self.conflict({'name':'RoutineDemandStatusConflict','message':'A demanda de rotina não está ativa.'})
  try:name=LocalProductStorage(directory='/tmp/django-routine-uploads').save(image)
  except ValueError as error:return self.bad_request({'name':'InputValidationError','message':str(error)})
  with transaction.atomic():
   demand.execution.new_module_image_url=name; demand.execution.observation=request.data.get('observation') or None; demand.execution.save()
   demand.status='FINISHED'; demand.save(update_fields=['status','updated_at'])
   expositions=ProductExpositionDetail.objects.filter(level__department_id=demand.module.planogram.department_id).select_related('product')
   stocks={(x.sku,x.ean):x.stock for x in BranchProductStock.objects.filter(branch_id=demand.branch_id)}
   ExecutionAudit.objects.bulk_create([ExecutionAudit(routine_execution=demand.execution,product_exposition=item,current_stock=stocks.get((item.product.sku,item.product.ean),0),non_exposition_reason='UNSUFICIENT_STOCK' if stocks.get((item.product.sku,item.product.ean),0)<item.min_stock else None) for item in expositions])
  return self.ok()


class UpdateRoutineExecutionStatusView(AuthenticatedController):
 authorized_roles=('ADMIN',)
 def patch(self,request):
  data=request.data
  if not isinstance(data,dict) or type(data.get('routineExecutionId')) is not int or data.get('status') not in ('APPROVED','REJECTED'):return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})
  execution=RoutineExecution.objects.select_related('routine_demand').filter(pk=data['routineExecutionId']).first()
  if not execution:return self.not_found({'name':'RoutineExecutionNotFound','message':f"A execução de rotina com id {data['routineExecutionId']} não foi encontrada."})
  if execution.status!='PENDING':return self.conflict({'name':'RoutineExecutionStatusUpdateConflict','message':f'Status atual é {execution.status}.'})
  if execution.routine_demand.status!='FINISHED':return self.conflict({'name':'UpdateRoutineExecutionStatusConflict','message':'A rotina ainda não foi concluída.'})
  execution.status=data['status'];execution.save(update_fields=['status','updated_at']);return self.ok()


def _routine(demand):
 execution=demand.execution
 return {'id':demand.id,'status':demand.status,'createdByUserId':demand.created_by_user_id,'branchId':demand.branch_id,'moduleId':demand.module_id,'layoutElementId':demand.layout_element_id,'createdAt':_iso(demand.created_at),'updatedAt':_iso(demand.updated_at),'execution':{'id':execution.id,'status':execution.status,'oldModuleImageUrl':execution.old_module_image_url,'newModuleImageUrl':execution.new_module_image_url,'observation':execution.observation,'executedByUserId':execution.executed_by_user_id,'routineDemandId':demand.id,'createdAt':_iso(execution.created_at),'updatedAt':_iso(execution.updated_at)}}


class RoutineDemandListView(AuthenticatedController):
 authorized_roles=('ADMIN','LAYOUT')
 def get(self,request,branch_id=None):
  rows=RoutineDemand.objects.select_related('execution').order_by('-created_at')
  if branch_id:
   if not branch_id.isdigit():return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})
   rows=rows.filter(branch_id=int(branch_id),status='ACTIVE')
   return self.ok({'results':[_routine(x) for x in rows]})
  try:page=int(request.query_params.get('pageNumber',1));size=int(request.query_params.get('pageSize',10))
  except ValueError:return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})
  status=request.query_params.get('demandStatus'); rows=rows.filter(status=status) if status in ('ACTIVE','FINISHED','EXPIRED') else rows
  total=rows.count();return self.ok({'totalPages':-(-total//size),'results':[_routine(x) for x in rows[(page-1)*size:page*size]]})


class RoutineExecutionListView(AuthenticatedController):
 authorized_roles=('ADMIN','LAYOUT','BRANCH')
 def get(self,request):
  try:page=int(request.query_params.get('pageNumber',1));size=int(request.query_params.get('pageSize',10))
  except ValueError:return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})
  rows=RoutineExecution.objects.select_related('routine_demand__branch','routine_demand__module__planogram__department').order_by('routine_demand_id')
  branch=request.query_params.get('branchId'); rows=rows.filter(routine_demand__branch_id=int(branch)) if branch and branch.isdigit() else rows
  status=request.query_params.get('status'); rows=rows.filter(status=status) if status in ('PENDING','APPROVED','REJECTED') else rows
  total=rows.count();results=[]
  for x in rows[(page-1)*size:page*size]:
   d=x.routine_demand; value={'id':x.id,'status':x.status,'oldModuleImageUrl':x.old_module_image_url,'newModuleImageUrl':x.new_module_image_url,'observation':x.observation,'executedByUserId':x.executed_by_user_id,'routineDemandId':d.id,'createdAt':_iso(x.created_at),'updatedAt':_iso(x.updated_at),'branch':{'id':d.branch.id,'name':d.branch.name}}
   if d.module_id:value['moduleDetails']={'id':d.module.id,'sequence':d.module.sequence,'planogramId':d.module.planogram_id,'department':{'id':d.module.planogram.department.id,'name':d.module.planogram.department.name}}
   results.append(value)
  return self.ok({'totalPages':-(-total//size),'results':results})


class RoutineExecutionDetailsView(AuthenticatedController):
 authorized_roles=('ADMIN','LAYOUT')
 def get(self,request,execution_id):
  if not execution_id.isdigit():return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})
  x=RoutineExecution.objects.select_related('executed_by_user','review').filter(pk=int(execution_id)).first()
  if not x:return self.not_found({'name':'RoutineExecutionNotFound','message':f'A execução de rotina com id {execution_id} não foi encontrada.'})
  user=x.executed_by_user; grouped={}
  for audit in x.audits.select_related('product_exposition__product','product_exposition__level'):
   e=audit.product_exposition
   if not e:continue
   item={'id':audit.id,'currentStock':audit.current_stock,'routineExecutionId':x.id,'productExpositionId':e.id}
   if audit.non_exposition_reason:item['nonExpositionReason']=audit.non_exposition_reason
   grouped.setdefault(e.level_id,{'levelId':e.level_id,'levelName':e.level.name,'audits':[]})['audits'].append(item)
  body={'id':x.id,'status':x.status,'score':x.score,'observation':x.observation,'oldModuleImageUrl':x.old_module_image_url,'newModuleImageUrl':x.new_module_image_url,'executedByUserId':x.executed_by_user_id,'routineDemandId':x.routine_demand_id,'createdAt':_iso(x.created_at),'updatedAt':_iso(x.updated_at),'executedByUser':{'id':user.id,'email':user.email,'name':user.name,'role':user.role,'isActive':user.is_active},'auditGroupedByLevel':list(grouped.values())}
  return self.ok({k:v for k,v in body.items() if v is not None})


class ReviewQuestionView(AuthenticatedController):
 authorized_roles=('ADMIN','LAYOUT','BRANCH')
 def get(self,request):
  return self.ok({'results':[{'id':q.id,'question':q.question,'scoreWeight':q.score_weight,'answers':[{'id':a.id,'name':a.name,'score':a.score} for a in q.answers.all()]} for q in ReviewQuestion.objects.prefetch_related('answers').all()]})


class CreateExecutionReviewView(AuthenticatedController):
 authorized_roles=('ADMIN',)
 def post(self,request):
  data=request.data
  if not isinstance(data,dict) or type(data.get('executionId')) is not int or data.get('demandType') not in ('ADMIN','ROUTINE') or not isinstance(data.get('answers'),list):return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})
  model=Execution if data['demandType']=='ADMIN' else RoutineExecution
  execution=model.objects.filter(pk=data['executionId']).first()
  if not execution:return self.not_found({'name':'ExecutionNotFoundError','message':'Execução não encontrada.'})
  if getattr(execution,'review_id',None):return self.conflict({'name':'ExecutionReviewAlreadyDone','message':'A execução já possui revisão.'})
  try:
   with transaction.atomic():
    review=ExecutionReview.objects.create(created_by_user_id=request.token_claims['sub'])
    weighted=[]
    for item in data['answers']:
     question=ReviewQuestion.objects.get(pk=item['questionId']); answer=ReviewAnswer.objects.get(pk=item['answerId'],question=question)
     ReviewQuestionAnswer.objects.create(execution_review=review,question=question,answer=answer,observation=item.get('observation'))
     weighted.append((answer.score,question.score_weight))
    score=round(sum(score*weight for score,weight in weighted)/sum(weight for _,weight in weighted)/10,2) if weighted else 0
    execution.review=review; execution.score=score; execution.save(update_fields=['review','score','updated_at'])
   return self.created({'score':score})
  except (KeyError,ReviewQuestion.DoesNotExist,ReviewAnswer.DoesNotExist,TypeError):return self.bad_request({'name':'InputValidationError','message':'Erro de validação'})


class DemandMetricsView(AuthenticatedController):
 def get(self,request):
  ufs=['PI','BA','RN','MA','PA']; branches={uf:0 for uf in ufs}; occ={}; exe={}
  for branch in Branch.objects.all():
   if branch.uf in branches:branches[branch.uf]+=1
  for row in ExecutionOccurrence.objects.select_related('demand_branch__branch'):
   uf=row.demand_branch.branch.uf; data=occ.setdefault(uf,[0,0]);data[0]+=1;data[1]+=row.status=='DONE'
  for row in Execution.objects.select_related('execution_occurrence__demand_branch__branch'):
   uf=row.execution_occurrence.demand_branch.branch.uf; data=exe.setdefault(uf,[0,0,0,0,0]);data[0]+=1;data[1]+=row.status=='REJECTED';data[2]+=row.score or 0;data[3]+=row.score is not None;data[4]+=(row.created_at-row.execution_occurrence.created_at).total_seconds()/86400
  values=[]
  for uf in ufs:
   total,done=occ.get(uf,[0,0]); et,rejected,sum_score,count_score,sum_days=exe.get(uf,[0,0,0,0,0]); values.append({'uf':uf,'branchesCount':branches[uf],'doneExecutionPercentage':round(done/total*100,2) if total else 0,'meanExecutionScore':round(sum_score/count_score,2) if count_score else 0,'rejectedExecutionPercentage':round(rejected/et*100,2) if et else 0,'meanExecutionTimeInDays':round(sum_days/et,1) if et else 0,'productivity':round(done/(branches[uf] or 1)*100,2) if total else 0})
  return self.ok({'metrics':sorted(values,key=lambda x:x['doneExecutionPercentage'],reverse=True)})
