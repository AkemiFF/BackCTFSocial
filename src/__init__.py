# myproject/__init__.py

from __future__ import absolute_import, unicode_literals

# Faire en sorte que Celery soit chargé quand Django démarre
from .celery import app as celery_app

__all__ = ('celery_app',)
