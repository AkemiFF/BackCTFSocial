import logging

from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Challenge, UserChallengeInstance
from .serializers import ChallengeSerializer
from .tasks import start_challenge_task

logger = logging.getLogger(__name__)

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import UserChallengeInstance


@api_view(['GET'])
def check_status(request, instance_id):
    instance = get_object_or_404(UserChallengeInstance, challenge_id=instance_id, user=request.user)
    
    instructions = f"Bienvenue dans le défi {instance.challenge.title}.\n{instance.challenge.description}"
    download_url = request.build_absolute_uri(
        reverse('download-ssh-key', args=[instance.id])
    )
    ssh_command = None
    if instance.challenge.challenge_type.slug == 'ssh' and '22/tcp' in instance.assigned_ports:
        ssh_command = (
            f"ssh -i cle_privee_{instance.id}.pem "
            f"ctf_user@{settings.DOCKER_HOST_IP} "
            f"-p {instance.assigned_ports['22/tcp']} "
            f"-o StrictHostKeyChecking=no"
        )
        
        instructions += (
            "\n\nPour vous connecter :\n"
            f"1. Téléchargez votre clé privée : [Lien de téléchargement]({download_url})\n"
            "2. Exécutez : chmod 600 cle_privee_*.pem\n"
            f"3. Utilisez : {ssh_command}"
        )

    return Response({
        'status': instance.status,
        'instructions': instructions,
        'ssh_download_url': download_url,
        'ssh_command': ssh_command
    })

@api_view(['GET'])
@require_http_methods(["GET"])
def download_ssh_key(request, instance_id):
    instance = get_object_or_404(UserChallengeInstance, id=instance_id, user=request.user)
    
    if not instance.ssh_credentials:
        return Response({"error": "Clé non disponible"}, status=404)

    # Création dynamique du fichier .pem
    private_key = instance.ssh_credentials.get('key')
    response = FileResponse(
        private_key,
        content_type='application/x-pem-file',
        as_attachment=True,
        filename=f'cle_privee_{instance.challenge.title}.pem'
    )
    return response

class ChallengeViewSet(viewsets.ModelViewSet):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_challenge(request, challenge_id):
    user = request.user
    challenge = get_object_or_404(Challenge, id=challenge_id)
    
    if UserChallengeInstance.objects.filter(user=user, challenge=challenge).exists():
        return Response({'error': 'Challenge déjà actif'}, status=400)

    try:
        # Crée l'instance et lance la tâche asynchrone
        instance = UserChallengeInstance.objects.create(
            user=user,
            challenge=challenge,
            unique_flag=challenge.generate_dynamic_flag(user),
            assigned_ports={}
        )
        
        start_challenge_task.delay(instance.id) 
        
        return Response({
            'status': 'processing',
            'message': 'Démarrage du challenge en cours...',
            'instance_id': str(instance.id)
        })
        
    except Exception as e:
        logger.error(f"Erreur démarrage challenge: {str(e)}")
        return Response({'error': str(e)}, status=500)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stop_challenge(request, challenge_id):
    instance = get_object_or_404(UserChallengeInstance, user=request.user, challenge_id=challenge_id)
    instance.stop_container()
    return Response({'status': 'stopped'})