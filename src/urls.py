# src/urls.py (mise à jour)
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/learning/', include('learning.urls')),
    path('api/challenges/', include('challenges.urls')),
    path('api/core/', include('core.urls')),
    path('api/social/', include('social.urls')),  # Ajout des URLs social
    # Autres URLs d'API
    path('api-auth/', include('rest_framework.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]