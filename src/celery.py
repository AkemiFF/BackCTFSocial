# src/celery.py

import os

from celery import Celery

# Définir le module de configuration Celery (Django settings)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')

app = Celery('src')

# Utiliser le backend de configuration Django pour configurer Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Charger automatiquement les tâches (tasks) de chaque application Django
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
