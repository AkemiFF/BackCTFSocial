# tests.py
import logging
from datetime import timedelta

import docker
from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from .models import (Challenge, ChallengeSubmission, ChallengeType,
                     DockerConfigTemplate, UserChallengeInstance,
                     generate_ssh_keys)

logger = logging.getLogger(__name__)
# tests.py
from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Challenge, ChallengeType, UserChallengeInstance

User = get_user_model()  # Récupère le modèle utilisateur personnalisé ou par défaut

class ChallengeModelTests(TestCase):
    def setUp(self):
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
             email="dudte@dqd.com"
        )
        
        # Créer le type de défi SSH
        self.ssh_type = ChallengeType.objects.create(
            name="SSH Test",
            slug="ssh_bk",
            validation_type="static",
            icon="terminal"
        )
        
        # Configuration Docker pour SSH
        DockerConfigTemplate.objects.create(
            challenge_type=self.ssh_type,
            dockerfile="FROM alpine:latest",
            default_ports=["22/tcp"],
            common_commands=[]
        )
        
        # Créer un défi exemple
        self.challenge = Challenge.objects.create(
            title="Test SSH Challenge",
            challenge_type=self.ssh_type,
            difficulty="easy",
            points=100,
            static_flag="FLAG{TEST_123}",
            docker_image="alpine:latest",
            docker_ports={"22/tcp": None},
        )

    def test_start_container(self):
        """Teste le démarrage d'un conteneur Docker."""
        self.challenge.build_docker_image()
        
        # Utiliser l'utilisateur créé dans setUp
        user_instance = UserChallengeInstance.objects.create(
            user=self.user,  # Correction ici
            challenge=self.challenge,
            unique_flag=self.challenge.static_flag
        )
        
        try:
            user_instance.start_container()
            self.assertEqual(user_instance.status, 'running')
        finally:
            user_instance.stop_container()

class UserChallengeInstanceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='webuser', email="dudte@dq.com",password='webpass')
        self.challenge_type = ChallengeType.objects.create(slug="web_test", name="Web Test")
        
    def test_container_lifecycle(self):
        challenge = Challenge.objects.create(
            title="Web Test",
            challenge_type=self.challenge_type,
            difficulty="easy",
            points=150,  # Champ manquant ajouté
            docker_image="nginx:alpine",
            docker_ports={"80/tcp": None},
            static_flag="FLAG{WEB_TEST}"
        )
        
        instance = UserChallengeInstance.objects.create(
            user=self.user,  # Utilisateur valide
            challenge=challenge,
            unique_flag="FLAG{WEB_TEST}"
        )
        
        try:
            instance.start_container()
            self.assertIsNotNone(instance.web_url)
        finally:
            instance.stop_container()
            
# Exécution des tests (avec pytest)
if __name__ == "__main__":
    import pytest
    pytest.main(["-v", "tests.py"])