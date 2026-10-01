from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from src.entities.demand.models import Demand, ExecutionOccurrence
from src.entities.notification.models import Notification
from src.entities.user.models import UserRoles, User


def advance(value, repetition):
    if repetition == 'DAILY': return value + timedelta(days=1)
    if repetition == 'WEEKLY': return value + timedelta(days=7)
    if repetition == 'BIWEEKLY': return value + timedelta(days=14)
    if repetition == 'MONTHLY':
        month = value.month % 12 + 1
        year = value.year + (value.month == 12)
        import calendar
        return value.replace(year=year, month=month, day=min(value.day, calendar.monthrange(year, month)[1]))
    return value


def occurrence_for_day(start_date, repetition, day):
    """Return the scheduled recurrence that belongs to ``day``, if any."""
    occurrence = start_date
    while advance(occurrence, repetition).date() <= day:
        occurrence = advance(occurrence, repetition)
    return occurrence if occurrence.date() == day else None


class Command(BaseCommand):
    help = 'Synchronizes pending execution occurrences for active demands.'

    def handle(self, *args, **options):
        now = timezone.now()
        expired = ExecutionOccurrence.objects.filter(status='PENDING', due_date__lt=now).update(status='EXPIRED')
        Demand.objects.filter(status='ACTIVE', end_date__lt=now).update(status='INACTIVE')
        created = 0
        with transaction.atomic():
            demands = Demand.objects.filter(status='ACTIVE', start_date__lte=now).prefetch_related('branches')
            for demand in demands:
                if demand.end_date and demand.end_date < now: continue
                for link in demand.branches.select_for_update():
                    if not demand.repetition_type:
                        next_date = demand.start_date
                        if link.last_execution_occurrences_sync_at or next_date.date() != now.date(): continue
                    else:
                        next_date = occurrence_for_day(demand.start_date, demand.repetition_type, now.date())
                        if not next_date or (demand.end_date and next_date > demand.end_date) or (link.last_execution_occurrences_sync_at and link.last_execution_occurrences_sync_at.date() == now.date()): continue
                    due = (next_date if demand.repetition_type else demand.end_date).replace(
                        hour=23, minute=59, second=59, microsecond=999000
                    )
                    ExecutionOccurrence.objects.create(demand_branch=link, due_date=due)
                    Notification.objects.bulk_create([Notification(user=user, message=f'Demanda {demand.title} está pendente na loja {link.branch_id}. Clique aqui e realize a comprovação!', data={'type':'NEW_DEMAND','demandId':demand.id,'demandTitle':demand.title,'branchId':link.branch_id,'branchName':link.branch.name,'redirectTo':'/branches/view-branch-layout'}) for user in User.objects.filter(role=UserRoles.BRANCH, branches__id=link.branch_id)])
                    link.last_execution_occurrences_sync_at = now; link.save(update_fields=['last_execution_occurrences_sync_at'])
                    created += 1
        self.stdout.write(f'Ocorrências: {created} criada(s), {expired} expirada(s).')
