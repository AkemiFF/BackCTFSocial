from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


class ChatHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    prompt = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    context = models.JSONField(default=dict)  # Pour stocker le contexte de session

    class Meta:
        ordering = ['-timestamp']