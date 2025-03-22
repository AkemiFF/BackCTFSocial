# signals.py
import logging
import uuid

from django.conf import settings
from django.db import transaction
# core/signals.py
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import Challenge, ChallengeType, DockerConfigTemplate


@receiver(post_migrate)
def setup_default_challenge_types(sender, **kwargs):
    """Crée les types de défis par défaut après la migration"""
    ChallengeType.objects.get_or_create(
        slug='ssh',
        defaults={
            'name': 'SSH Challenge',
            'validation_type': 'command',
            'icon': 'terminal'
        }
    )

    ChallengeType.objects.get_or_create(
        slug='web',
        defaults={
            'name': 'Web Challenge',
            'validation_type': 'file_hash',
            'icon': 'globe'
        }
    )

    ChallengeType.objects.get_or_create(
        slug='crypto',
        defaults={
            'name': 'Cryptographie',
            'validation_type': 'static',
            'icon': 'lock'
        }
    )

logger = logging.getLogger(__name__)

@receiver(post_migrate)
def setup_initial_data(sender, **kwargs):
    """Initialise les données système après les migrations"""
    if sender and sender.name == 'ctf':  # Remplacez 'core' par le nom de votre app
        create_default_challenge_types()
        create_sample_challenges()

@receiver(post_save, sender=Challenge)
def build_challenge_image(sender, instance, created, **kwargs):
    if created and not instance.built_image:
        success = instance.build_docker_image()
        if not success:
            instance.delete()  # Rollback si échec
            raise Exception("Échec de la construction de l'image Docker")
        
def create_default_challenge_types():
    """Crée les types de défis de base"""
    types = [
        ('ssh', 'SSH Challenge', 'command', 'terminal'),
        ('web', 'Web Challenge', 'file_hash', 'globe'),
        ('crypto', 'Cryptographie', 'static', 'lock')
    ]
    
    for slug, name, validation, icon in types:
        obj, created = ChallengeType.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'validation_type': validation,
                'icon': icon
            }
        )
        if created:
            logger.info(f"ChallengeType créé : {slug}")

def create_sample_challenges():
    """Crée des défis exemple si aucun n'existe"""
    if Challenge.objects.exists():
        return

    samples = [
         {
            'title': 'SSH Débutant',
            'type_slug': 'ssh',
            'difficulty': 'easy',
            'points': 100,
            'description': 'Trouvez le flag caché dans /home/ctf_user',
            'static_flag': 'FLAG{SSH_MASTER_123}'  # Flag explicite
        },       
        {
            'title': 'Web Basic',
            'type_slug': 'web',
            'difficulty': 'easy',
            'points': 150,
            'description': 'Inspectez le code source de la page web'
        }
    ]

    for data in samples:
        try:
            with transaction.atomic():
                challenge_type = ChallengeType.objects.get(slug=data['type_slug'])
                challenge = Challenge.objects.create(
                    title=data['title'],
                    challenge_type=challenge_type,
                    difficulty=data['difficulty'],
                    points=data['points'],
                    description=data['description']
                )
                logger.info(f"Challenge exemple créé : {challenge.title}")
        except Exception as e:
            logger.error(f"Erreur création challenge : {str(e)}")

@receiver(post_save, sender=Challenge)
def handle_challenge_creation(sender, instance, created, **kwargs):
    """Gère la configuration automatique des nouveaux défis"""
    if created:
        try:
            configure_new_challenge(instance)
            logger.info(f"Challenge configuré : {instance.title}")
        except Exception as e:
            logger.error(f"Erreur configuration challenge {instance.id}: {str(e)}")
            instance.delete()  # Rollback si échec
            raise

def configure_new_challenge(challenge):
    """Applique la configuration automatique"""
    # Génération du flag
    if not challenge.static_flag:
        challenge.static_flag = f"FLAG_{uuid.uuid4().hex[:16].upper()}"
    
    challenge.environment_vars = settings.HACKITECH_BASE_CONFIG.get(
        challenge.challenge_type.slug, {}
    ).get(challenge.difficulty, {}).get('environment', {})
    
    base_config = settings.HACKITECH_BASE_CONFIG.get(
        challenge.challenge_type.slug, {}
    ).get(challenge.difficulty, {})
    
    challenge.docker_image = base_config.get('image', 'alpine:latest')
    challenge.docker_ports = base_config.get('ports', {'80/tcp': None})
    challenge.environment_vars = base_config.get('environment', {})
    challenge.startup_command = base_config.get('command', '')
    
    # Validation des données
    if not challenge.docker_image:
        raise ValueError("Image Docker non configurée pour ce type/difficulté")
    
    # Sauvegarde finale
    challenge.save()