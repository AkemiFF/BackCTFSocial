import logging

from django.db import transaction
from django.shortcuts import get_object_or_404, render
# Create your views here.
# api/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Challenge, UserChallengeInstance

# Configuration du logger
logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_challenge(request, challenge_id):
    user = request.user
    challenge = get_object_or_404(Challenge, id=challenge_id)
    
    if UserChallengeInstance.objects.filter(user=user, challenge=challenge).exists():
        return Response({'error': 'Challenge déjà actif'}, status=400)

    try:
        with transaction.atomic():
            instance = UserChallengeInstance.objects.create(
                user=user,
                challenge=challenge,
                unique_flag=challenge.generate_dynamic_flag(user),
                assigned_ports={}  # Valeur par défaut explicite
            )
            instance.start_container()
            
            return Response({
                'status': 'success',
                'connection_info': instance.connection_info()
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