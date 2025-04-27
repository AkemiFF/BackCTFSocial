# tasks.py
import logging

import docker

from celery import shared_task

from .models import UserChallengeInstance

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    autoretry_for=(docker.errors.APIError, docker.errors.ImageNotFound),
    retry_backoff=10,
    max_retries=2
)
def start_challenge_task(self, instance_id):
    try:
        instance = UserChallengeInstance.objects.get(id=instance_id)
        logger.info(f"Tâche {self.request.id} - Démarrage conteneur {instance_id}")
        
        instance.start_container()
        
        return {
            "status": "success",
            "instance_id": instance_id,
            "container_id": instance.container_id
        }
        
    except Exception as e:
        logger.error(f"Échec tâche {self.request.id} : {str(e)}")
        instance.status = 'failed'
        instance.save()
        raise self.retry(exc=e, countdown=30)