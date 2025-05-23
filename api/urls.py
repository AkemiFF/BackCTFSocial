# api/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .docs.views import (CachedSpectacularAPIView,
                         ProtectedSpectacularRedocView,
                         ProtectedSpectacularSwaggerView)
from .views import (AdminTokenRefreshView, ApiRootView,
                    CustomTokenObtainPairView, api_user_info)

# API router
router = DefaultRouter()
from accounts import views

urlpatterns = [
    # API root
    # path('', ApiRootView.as_view(), name='api-root'),
    
    # Authentication
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/refresh/admin/', AdminTokenRefreshView.as_view(), name='admin_token_refresh'),  
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/user/', api_user_info, name='api_user_info'),
    path('auth/register/initiate/', views.initiate_registration, name='initiate_registration'),
    path('auth/register/complete/', views.complete_registration, name='complete_registration'),

    # Documentation
    path('schema/', CachedSpectacularAPIView.as_view(), name='schema'),
    path('docs/', ProtectedSpectacularSwaggerView.as_view(url_name='schema'), name='schema-swagger-ui'),
    path('redoc/', ProtectedSpectacularRedocView.as_view(url_name='schema'), name='schema-redoc'),
    
    # Include other app URLs
    path('accounts/', include('accounts.urls')),
    path('challenges/', include('challenges.urls')),
    path('core/', include('core.urls')),
    path('social/', include('social.urls')),
    path('messaging/', include('messaging.urls')),
    path('teams/', include('teams.urls')),
    path('gamification/', include('gamification.urls')),
    path('notifications/', include('notifications.urls')),
]