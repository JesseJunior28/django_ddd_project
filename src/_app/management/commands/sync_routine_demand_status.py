from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from src.entities.routine.models import RoutineDemand


class Command(BaseCommand):
    help = 'Expires active routine demands older than 24 hours.'
    def handle(self,*args,**options):
        expired=RoutineDemand.objects.filter(status='ACTIVE',created_at__lt=timezone.now()-timedelta(hours=24)).update(status='EXPIRED')
        self.stdout.write(f'Rotinas: {expired} expirada(s).')
