# api/views.py
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)


class ApiRootView(APIView):
    """
    Root view for the API, listing all available endpoints.
    """
    def get(self, request, format=None):
        data = {
            'accounts': request.build_absolute_uri(reverse('accounts-api-root')),
            'learning': request.build_absolute_uri(reverse('learning-api-root')),
            'challenges': request.build_absolute_uri(reverse('challenges-api-root')),
            'core': request.build_absolute_uri(reverse('core-api-root')),
            'social': request.build_absolute_uri(reverse('social-api-root')),
            'messaging': request.build_absolute_uri(reverse('messaging-api-root')),
            'teams': request.build_absolute_uri(reverse('teams-api-root')),
            'gamification': request.build_absolute_uri(reverse('gamification-api-root')),
            'notifications': request.build_absolute_uri(reverse('notifications-api-root')),
            'docs': request.build_absolute_uri(reverse('schema-swagger-ui')),
        }
        return Response(data)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that adds additional information to the response.
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            # Add user info to response
            user = request.user
            response.data['user_id'] = user.id
            response.data['username'] = user.username
            response.data['email'] = user.email
            response.data['role'] = user.role
            
            # Add token expiration info
            response.data['token_lifetime'] = {
                'access': f"{settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()} seconds",
                'refresh': f"{settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()} seconds",
            }
        
        return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_user_info(request):
    """
    Return information about the authenticated user.
    """
    user = request.user
    data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'is_staff': user.is_staff,
        'is_active': user.is_active,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
    }
    
    # Add API-specific information if available
    try:
        from accounts.models import ApiKey, ApiScope
        api_keys = ApiKey.objects.filter(user=user, is_active=True)
        api_scopes = ApiScope.objects.filter(user=user, is_active=True)
        
        data['api_keys'] = [
            {
                'key_id': key.id,
                'name': key.name,
                'created_at': key.created_at,
                'last_used': key.last_used,
            } for key in api_keys
        ]
        
        data['api_scopes'] = [scope.scope for scope in api_scopes]
    except:
        pass
    
    return Response(data)