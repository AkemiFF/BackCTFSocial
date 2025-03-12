# api/docs/views.py
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.views import (SpectacularAPIView, SpectacularRedocView,
                                   SpectacularSwaggerView)
from rest_framework.permissions import IsAuthenticated


class CachedSpectacularAPIView(SpectacularAPIView):
    """
    Cached version of SpectacularAPIView to improve performance.
    """
    @method_decorator(cache_page(60 * 60))  # Cache for 1 hour
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ProtectedSpectacularSwaggerView(SpectacularSwaggerView):
    """
    Swagger UI view that requires authentication.
    """
    permission_classes = [IsAuthenticated]


class ProtectedSpectacularRedocView(SpectacularRedocView):
    """
    ReDoc view that requires authentication.
    """
    permission_classes = [IsAuthenticated]