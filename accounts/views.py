import re
import secrets
import string
from collections import defaultdict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (RegistrationRequest, User, UserFollowing, UserProfile,
                     UserProjects, UserSession)
from .permissions import IsOwnerOrReadOnly, IsUserOrAdmin
from .serializers import *


class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LeaderboardUserSerializer

    def get_queryset(self):
        return (
            User.objects
            .annotate(
                num_completed=Count(
                'challenge_submissions',
                filter=Q(challenge_submissions__is_correct=True),
                distinct=True
                )
            )        
            .order_by('-points')
        )

class UserProfileDetailsViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserDetailsSerializer  
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'delete'] 
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return User.objects.prefetch_related('projects').filter(id=self.request.user.id)

    def get_object(self):
        return self.request.user

    def convert_querydict(self, querydict):
        """
        Convertit le QueryDict en dictionnaire Python standard.
        Pour chaque clé, si plusieurs valeurs existent, on garde la liste,
        sinon on conserve la valeur unique.
        """
        data = {}
        for key in querydict.keys():
            values = querydict.getlist(key)
            data[key] = values if len(values) > 1 else values[0]
        return data

    def parse_nested_field(self, data, prefix):
        """
        Transforme les clés du type prefix[field] et prefix[field][index]
        en un dictionnaire imbriqué.
        Exemple pour profile :
            "profile[display_name]": "Alex Durand"
            "profile[skills][0]": "bf505b49-8361-424d-ac1f-11424ed387b1"
            "profile[skills][1]": "9ca97f75-7133-46cf-89bb-ee3671954415"
        deviendra :
            "display_name": "Alex Durand",
            "skills": ["bf505b49-8361-424d-ac1f-11424ed387b1", "9ca97f75-7133-46cf-89bb-ee3671954415"]
        """
        nested = {}
        # Récupère les clés qui commencent par prefix[
        keys_to_remove = [key for key in data.keys() if key.startswith(prefix + '[')]
        # Pattern pour les champs en liste : profile[skills][0]
        list_pattern = re.compile(r'^' + re.escape(prefix) + r'\[([^\]]+)\]\[(\d+)\]$')
        # Pattern pour les champs simples : profile[display_name]
        field_pattern = re.compile(r'^' + re.escape(prefix) + r'\[([^\]]+)\]$')
        for key in keys_to_remove:
            value = data.pop(key)
            list_match = list_pattern.match(key)
            if list_match:
                field_name = list_match.group(1)
                index = int(list_match.group(2))
                if field_name not in nested:
                    nested[field_name] = {}
                nested[field_name][index] = value
            else:
                field_match = field_pattern.match(key)
                if field_match:
                    field_name = field_match.group(1)
                    nested[field_name] = value
        # Convertir les dictionnaires à clés numériques en liste ordonnée
        for field_name, val in nested.items():
            if isinstance(val, dict) and all(isinstance(k, int) for k in val.keys()):
                nested[field_name] = [val[k] for k in sorted(val.keys())]
        return nested

    def parse_nested_projects(self, data):
        """
        Transforme les clés du type user_projects[0][champ] en une liste de dictionnaires.
        """
        projects = defaultdict(dict)
        pattern = re.compile(r'^user_projects\[(\d+)\]\[(.+)\]$')
        for key, value in data.items():
            match = pattern.match(key)
            if match:
                index = int(match.group(1))
                field = match.group(2)
                projects[index][field] = value
        return list(projects.values())

    def update(self, request, *args, **kwargs):
        # Convertir le QueryDict en dictionnaire Python standard
        data = self.convert_querydict(request.data)
        
        # Transformer les clés imbriquées pour "profile" (y compris skills)
        if any(key.startswith('profile[') for key in data.keys()):
            data['profile'] = self.parse_nested_field(data, 'profile')
        
        # Transformer les clés imbriquées pour "user_projects" en liste de dictionnaires
        if any(key.startswith('user_projects[') for key in data.keys()):
            data['user_projects'] = self.parse_nested_projects(data)
            print("user_projects transformées:", data['user_projects'])
        
        print("Données transformées :", data)
        
        serializer = self.get_serializer(
            self.get_object(), data=data, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsUserOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_verified']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'bio']
    ordering_fields = ['username', 'date_joined', 'points']
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        user = self.get_object()
        if user == request.user:
            return Response(
                {"detail": "You cannot follow yourself."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        following, created = UserFollowing.objects.get_or_create(
            user=request.user,
            following_user=user
        )
        
        if created:
            return Response(
                {"detail": f"You are now following {user.username}."}, 
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"detail": f"You are already following {user.username}."}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def unfollow(self, request, pk=None):
        user = self.get_object()
        try:
            following = UserFollowing.objects.get(
                user=request.user,
                following_user=user
            )
            following.delete()
            return Response(
                {"detail": f"You have unfollowed {user.username}."}, 
                status=status.HTTP_200_OK
            )
        except UserFollowing.DoesNotExist:
            return Response(
                {"detail": f"You are not following {user.username}."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def following(self, request):
        following = UserFollowing.objects.filter(user=request.user)
        page = self.paginate_queryset(following)
        if page is not None:
            serializer = UserFollowingSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = UserFollowingSerializer(following, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def followers(self, request):
        followers = UserFollowing.objects.filter(following_user=request.user)
        page = self.paginate_queryset(followers)
        if page is not None:
            serializer = UserFollowingSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = UserFollowingSerializer(followers, many=True)
        return Response(serializer.data)


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=self.request.user)


class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return UserSession.objects.all()
        return UserSession.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        session = self.get_object()
        if session.user != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to terminate this session."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        session.is_active = False
        session.save()
        return Response(
            {"detail": "Session terminated successfully."}, 
            status=status.HTTP_200_OK
        )
        
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def initiate_registration(request):
    # print("Corps de la requête reçu :", request.data)  # Décode le corps brut en chaîne de caractères
    serializer = InitiateRegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    email = User.objects.normalize_email(serializer.validated_data['email'])
    
    # Vérifier si l'email existe déjà
    if User.objects.filter(email=email).exists():
        return Response({"error": "Email déjà enregistré"}, status=400)
    
    # Générer un code de 6 chiffres
    code = ''.join(secrets.choice(string.digits) for _ in range(6))
    
    # Créer ou mettre à jour la demande d'inscription
    RegistrationRequest.objects.update_or_create(
        email=email,
        defaults={'code': code, 'created_at': timezone.now()}
    )
    
    # Envoyer le code par email (à remplacer par une tâche asynchrone en production)
    send_mail(
        'Votre code de vérification HackITech',
        f'Votre code de vérification est : {code}',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
    
    return Response({"message": "Code de vérification envoyé par email"})

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def complete_registration(request):
    serializer = CompleteRegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    
    email = User.objects.normalize_email(serializer.validated_data['email'])
    code = serializer.validated_data['code']
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    
    # Récupérer la demande d'inscription
    try:
        registration_request = RegistrationRequest.objects.filter(email=email).latest('created_at')
    except RegistrationRequest.DoesNotExist:
        print("Aucune demande d'inscription trouvée pour l'email:", email)
        return Response({"error": "Aucune demande d'inscription trouvée"}, status=400)
    
    # Vérifier le code et l'expiration
    if registration_request.code != code:
        print("Code invalide pour l'email:", email)
        return Response({"error": "Code invalide"}, status=400)
    
    if registration_request.is_expired():
        
        print("Code expiré pour l'email:", email)
        return Response({"error": "Code expiré"}, status=400)
    
    # Vérifier le nom d'utilisateur
    if User.objects.filter(username=username).exists():
        print("Nom d'utilisateur déjà pris:", username)
        return Response({"error": "Nom d'utilisateur déjà pris"}, status=505)
    
    # Créer l'utilisateur
    try:
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            is_verified=True
        )
    except IntegrityError:
        return Response({"error": "Erreur lors de la création du compte"}, status=400)
    
    # Supprimer la demande d'inscription
    registration_request.delete()
    
    return Response({
        "message": "Compte créé avec succès",
        "user_id": user.id,
        "email": user.email,
        "username": user.username
    })