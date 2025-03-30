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

from .models import Challenge, ChallengeType, UserChallengeInstance
from .serializers import *
from .tasks import start_challenge_task

logger = logging.getLogger(__name__)

import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import (Challenge, ChallengeCategory, ChallengeType,
                     DockerConfigTemplate, UserChallengeInstance)
from .serializers import (ChallengeCategorySerializer, ChallengeSerializer,
                          ChallengeTypeSerializer,
                          DockerConfigTemplateSerializer)

logger = logging.getLogger(__name__)

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


class ChallengeTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChallengeType.objects.all()
    serializer_class = ChallengeTypeSerializer
    permission_classes = [IsAuthenticated]

class DockerConfigTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DockerConfigTemplate.objects.all()
    serializer_class = DockerConfigTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = DockerConfigTemplate.objects.all()
        challenge_type = self.request.query_params.get('challenge_type', None)
        
        if challenge_type:
            queryset = queryset.filter(challenge_type__slug=challenge_type)
            
        return queryset

class ChallengeCategoryViewSet(viewsets.ModelViewSet):
    queryset = ChallengeCategory.objects.all()
    serializer_class = ChallengeCategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
class DockerConfigTemplateCreateViewSet(viewsets.ModelViewSet):
    queryset = DockerConfigTemplate.objects.all()
    serializer_class = DockerConfigTemplateCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

class ChallengeViewSet(viewsets.ModelViewSet):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'build_image']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        queryset = Challenge.objects.all()
        challenge_type = self.request.query_params.get('challenge_type', None)
        difficulty = self.request.query_params.get('difficulty', None)
        category = self.request.query_params.get('category', None)
        is_active = self.request.query_params.get('is_active', None)
        
        if challenge_type:
            queryset = queryset.filter(challenge_type__slug=challenge_type)
        
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        if category:
            queryset = queryset.filter(challengecategory__id=category)
        
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def build_image(self, request, pk=None):
        challenge = self.get_object()
        
        try:
            success = challenge.build_docker_image()
            if success:
                return Response({"status": "success", "message": "Docker image built successfully"})
            else:
                return Response(
                    {"status": "error", "message": "Failed to build Docker image"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(f"Error building Docker image: {str(e)}")
            return Response(
                {"status": "error", "message": f"Error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['GET'])
def docker_templates_view(request):
    """
    Endpoint pour récupérer toutes les données nécessaires à la page d'ajout de défi
    """
    challenge_types = ChallengeType.objects.all()
    docker_templates = DockerConfigTemplate.objects.all()
    categories = ChallengeCategory.objects.all()
    
    data = {
        'challenge_types': ChallengeTypeSerializer(challenge_types, many=True).data,
        'docker_templates': DockerConfigTemplateSerializer(docker_templates, many=True).data,
        'categories': ChallengeCategorySerializer(categories, many=True).data,
        'difficulty_levels': dict(Challenge.DIFFICULTY_LEVELS)
    }
    
    return Response(data)


    
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