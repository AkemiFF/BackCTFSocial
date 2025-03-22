# core/tasks.py
from celery import shared_task
from django.utils import timezone

from ..ctf.models import UserChallengeInstance


@shared_task
def cleanup_expired_instances():
    """Nettoie les instances expirées toutes les 15 minutes"""
    expired = UserChallengeInstance.objects.filter(
        expiry_time__lte=timezone.now()
    )
    
    for instance in expired:
        instance.stop_container()
        instance.delete()

@shared_task
def health_check_instances():
    """Vérifie l'état des conteneurs toutes les 5 minutes"""
    instances = UserChallengeInstance.objects.filter(status='running')
    
    for instance in instances:
        if not instance.is_running():
            instance.status = 'error'
            instance.save()