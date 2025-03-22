import json
import logging
import os
import tempfile
import time
import uuid

import docker
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .docker import docker_manager

logger = logging.getLogger(__name__)


def generate_ssh_keys():
    """Génère une paire de clés SSH RSA"""
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    private_key = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    public_key = key.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    ).decode('utf-8')
    
    return private_key, public_key

class ChallengeType(models.Model):
    """Types de défis disponibles (SSH, Web, Crypto, etc.)"""
    name = models.CharField(_('name'), max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    validation_type = models.CharField(max_length=20, choices=[
        ('static', 'Flag statique'),
        ('command', 'Sortie de commande'),
        ('file_hash', 'Hash de fichier')
    ])
    icon = models.CharField(max_length=50, default='terminal')

    def __str__(self):
        return self.name

class DockerConfigTemplate(models.Model):
    """Modèles de configuration Docker par type de défi"""
    challenge_type = models.ForeignKey(ChallengeType, on_delete=models.CASCADE)
    dockerfile = models.TextField(_('dockerfile'))
    default_ports = models.JSONField(default=list)
    common_commands = models.JSONField(default=list)

    class Meta:
        verbose_name = _('Docker Template')

class Challenge(models.Model):
    """Défi CTF avec configuration dynamique"""
    DIFFICULTY_LEVELS = (
        ('easy', 'Facile'),
        ('medium', 'Moyen'),
        ('hard', 'Difficile')
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('title'), max_length=200)
    challenge_type = models.ForeignKey(ChallengeType, on_delete=models.PROTECT)
    difficulty = models.CharField(_('difficulty'), max_length=20, choices=DIFFICULTY_LEVELS)
    description = models.TextField(_('description'))
    points = models.PositiveIntegerField(_('points'))
    
    # Configuration Docker dynamique
    docker_image = models.CharField(_('docker image'), max_length=255)
    docker_ports = models.JSONField(_('ports'), default=dict)
    environment_vars = models.JSONField(_('environment'), default=dict)
    startup_command = models.CharField(_('start command'), max_length=255, blank=True)
    
    # Flags et validation
    static_flag = models.CharField(_('static flag'), max_length=255, blank=True)
    flag_generation_script = models.TextField(_('flag script'), blank=True)
    validation_script = models.TextField(_('validation script'), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(_('active'), default=True)
    dockerfile = models.TextField(_('dockerfile'), blank=True)
    docker_context = models.JSONField(_('contexte Docker'), default=dict)
    built_image = models.CharField(_('image construite'), max_length=255, blank=True)
    
    def build_docker_image(self):
        """Construit l'image Docker dynamiquement"""
        client = docker.from_env()
        image_tag = f"hackitech/{self.id}:latest"
        
        with tempfile.TemporaryDirectory() as context_dir:
            # Générer le Dockerfile
            dockerfile_content = self.dockerfile or self.generate_default_dockerfile()
            dockerfile_path = os.path.join(context_dir, "Dockerfile")
            with open(dockerfile_path, "w") as f:
                f.write(dockerfile_content)
            
            # Générer automatiquement flag.txt si nécessaire
            if "COPY flag.txt" in dockerfile_content:
                flag_path = os.path.join(context_dir, "flag.txt")
                with open(flag_path, "w") as f:
                    f.write(self.static_flag)
            
            # Copier les fichiers personnalisés
            for filename, content in self.docker_context.get('files', {}).items():
                file_path = os.path.join(context_dir, filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w") as f:
                    f.write(content)
            
            # Construction de l'image
            try:
                image, logs = client.images.build(
                    path=context_dir,
                    tag=image_tag,
                    buildargs=self.docker_context.get('args', {}),
                    forcerm=True
                )
                self.built_image = image_tag
                self.save()
                
                # Journalisation des logs de construction
                for chunk in logs:
                    if 'stream' in chunk:
                        logger.debug(chunk['stream'].strip())
                return True
           
            except docker.errors.BuildError as e:
                logger.error(f"Échec du build : {e.msg}\nLogs : {e.build_log}")
                return False
            
        # Dans models.py, méthode generate_default_dockerfile()
    def generate_default_dockerfile(self):
        if self.challenge_type.slug == 'ssh':
            return """
            FROM alpine:latest

            # Installation de SSH et configuration
            RUN apk add --no-cache openssh-server shadow && \
                ssh-keygen -A && \
                mkdir -p /var/run/sshd && \
                adduser -D -h /home/ctf_user -s /bin/sh ctf_user && \
                sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config && \
                sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config && \
                sed -i 's/AllowTcpForwarding no/AllowTcpForwarding yes/' /etc/ssh/sshd_config

            EXPOSE 22
            CMD ["sh", "-c", "which sshd && /usr/sbin/sshd -D -e"]
            """
        elif self.challenge_type.slug == 'web':
            return """
            FROM nginx:alpine
            CMD ["nginx", "-g", "daemon off;"]  # Main process
            """
        return "FROM alpine:latest"

    class Meta:
        ordering = ['difficulty', 'title']
    
    def __str__(self):
        return f"{self.title} ({self.get_difficulty_display()})"
    
    def generate_dynamic_flag(self, user):
        """Génère un flag unique pour l'utilisateur"""
        if self.challenge_type.validation_type == 'static':
            return self.static_flag
            
        return f"FLAG{{{user.id}_{self.id}_{uuid.uuid4().hex[:8]}}}"
    
    def save(self, *args, **kwargs):
        if isinstance(self.environment_vars, str):
            try:
                json.loads(self.environment_vars)  # Validation JSON
            except json.JSONDecodeError:
                raise ValueError("Format JSON invalide pour environment_vars")
        super().save(*args, **kwargs)
        
class UserChallengeInstance(models.Model):
    """Instance Docker par utilisateur pour un défi"""
    STATUS_CHOICES = (
        ('running', 'En cours'),
        ('stopped', 'Arrêté'),
        ('expired', 'Expiré')
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    container_id = models.CharField(_('container ID'), max_length=64)
    assigned_ports = models.JSONField(_('ports assignés'), default=dict)
    ssh_credentials = models.JSONField(_('accès SSH'), blank=True, null=True)
    web_url = models.URLField(_('URL web'), blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    unique_flag = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('user', 'challenge')
    
    def save(self, *args, **kwargs):
        if not self.expiry_time:
            self.expiry_time = timezone.now() + timezone.timedelta(hours=2)
        super().save(*args, **kwargs)
    
    
    def connection_info(self):
        """Retourne les infos de connexion selon le type de défi"""
        if self.challenge.challenge_type.slug == 'ssh':
            return {
                'host': settings.DOCKER_HOST_IP,
                'port': self.assigned_ports.get('22/tcp'),
                'username': 'ctf_user',
                'auth_method': 'ssh_key' if self.ssh_credentials else 'password'
            }
        elif self.challenge.challenge_type.slug == 'web':
            return {'url': self.web_url}
        return {}
    
    def start_container(self):
        """Lance le conteneur Docker avec configuration dynamique"""
        challenge = self.challenge
        user_prefix = f"{self.user.id}_{self.challenge.id}"
        docker_manager.ensure_network()

        # Génération des paramètres dynamiques
        container_config = {
            'image': self.challenge.built_image,  
            'detach': True,  # Syntaxe corrigée
            'network_mode': docker_manager.network_name, 
            'name': f"{user_prefix}_{uuid.uuid4().hex[:8]}",
            'ports': self._get_port_bindings(), 
            'environment': {
                        **self._get_environment_vars(),
                        'SSHD_OPTS': '-D -e'  # Force le mode démon + logging
                    },            
            
            # 'remove': True ,
            # Retirez temporairement les limites de ressources
            # 'mem_limit': '512m',
            # 'cpu_quota': 50000,
            'restart_policy': {"Name": "unless-stopped"}, 
            'labels': {
                'hackitech_user': str(self.user.id),
                'hackitech_challenge': str(self.challenge.id)
            }
        }
        
        try:
            container = docker_manager.client.containers.run(**container_config)
            # container.reload()

            for line in container.logs(stream=True):
                logger.debug(line.decode().strip())
            
            start_time = time.time()
            while container.status != 'running' or (time.time() - start_time) < 10:
                time.sleep(0.5)
                container.reload()

            if container.status != 'running':
                error_logs = container.logs().decode()
                logger.error(f"Le conteneur n'a pas démarré correctement. Logs:\n{error_logs}")
                raise RuntimeError("Le conteneur n'a pas démarré correctement")

            self.container_id = container.id
            self.assigned_ports = self._sanitize_ports(container.ports)
            self._post_start_setup(container)
            self.status = 'running'
            self.save()
        except docker.errors.ContainerError as e:
            logger.error(f"Erreur lors de l'exécution du conteneur : {str(e)}")
            raise
        except docker.errors.ImageNotFound as e:
            logger.error(f"Image Docker introuvable : {str(e)}")
            raise
        except docker.errors.APIError as e:
            logger.error(f"Erreur API Docker : {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors du démarrage du conteneur : {str(e)}")
            raise

        
    def _sanitize_ports(self, docker_ports):
        """Convertit la structure Docker en dict simple"""
        sanitized = {}
        if docker_ports:
            for container_port, host_configs in docker_ports.items():
                if host_configs and isinstance(host_configs, list):
                  sanitized[container_port] = str(host_configs[0].get('HostPort', ''))
        return sanitized
    
    def _get_environment_vars(self):
        """Injecte les variables dynamiques"""
        # Conversion JSON -> dict si nécessaire
        base_vars = self.challenge.environment_vars
        if isinstance(base_vars, str):
            base_vars = json.loads(base_vars)
        
        return {
            **base_vars,
            'FLAG': self.unique_flag,
            'USER_ID': str(self.user.id),
            'CHALLENGE_ID': str(self.challenge.id)
        }

    def _get_port_bindings(self):
        """Configure les ports avec le format Docker SDK"""
        port_bindings = {}
        for container_port, host_port in self.challenge.docker_ports.items():
            # Format : {'22/tcp': [{'HostPort': ''}]} pour un port dynamique
            port_bindings[container_port] = (
                [docker.types.PortBinding(HostPort=host_port or '')] 
                if host_port else None
            )
        return port_bindings

    def _post_start_setup(self, container):
        """Configuration post-démarrage"""
        if self.challenge.challenge_type.slug == 'ssh':
            self._setup_ssh_access(container)
        elif self.challenge.challenge_type.slug == 'web':
            self._setup_web_access(container)

    def _setup_ssh_access(self, container):
        
        """Configure l'accès SSH unique"""
        private_key, public_key = generate_ssh_keys()
        exit_code, output = container.exec_run(
            f"sh -c 'mkdir -p /home/ctf_user/.ssh && "
            f"echo \"{public_key}\" > /home/ctf_user/.ssh/authorized_keys && "
            f"chmod 700 /home/ctf_user/.ssh && "
            f"chmod 600 /home/ctf_user/.ssh/authorized_keys'",
            user="root"
        )
        
        if exit_code != 0:
            raise RuntimeError(f"Échec configuration SSH : {output.decode()}")
        
        
        try:
            if container.status != 'running':
                container.start()
                time.sleep(2)                  
            
            if exit_code != 0:
                raise RuntimeError(f"Échec SSH setup: {output.decode()}")
        except Exception as e:
            logger.error(f"Erreur configuration SSH: {str(e)}")
            raise
        SSHKey.objects.create(
            user_instance=self,
            private_key=private_key,
            public_key=public_key
        )
        
        # encryptor = get_crypt()
        self.ssh_credentials = {
            'port': self.assigned_ports['22/tcp'],
            'username': 'ctf_user',
            'key': private_key.encode()
        }
        self.save()

    def stop_container(self):
        """Arrête et nettoie le conteneur"""
        if self.container_id:
            try:
                container = docker_manager.client.containers.get(self.container_id)
                container.stop(timeout=10)
                container.remove()
                self.status = 'stopped'
                self.save()
            except docker.errors.NotFound:
                self.status = 'expired'
                self.save()

    def is_running(self):
        """Vérifie l'état actuel du conteneur"""
        try:
            container = docker_manager.client.containers.get(self.container_id)
            return container.status == 'running'
        except:
            return False
        # models.py (classe UserChallengeInstance)
    def _setup_web_access(self, container):
        
        """Configure l'accès web dynamique"""
        # Récupère l'URL basée sur le port exposé
        host_port = self.assigned_ports.get('80/tcp') or self.assigned_ports.get('443/tcp')
        
        if host_port:
            self.web_url = f"http://{settings.DOCKER_HOST_IP}:{host_port}"
        else:
            self.web_url = f"http://{container.name}.{docker_manager.network_name}"
        
        # Injecte le flag dans le conteneur web
        container.exec_run(
            f"sh -c 'echo \"{self.unique_flag}\" > /usr/share/nginx/html/flag.txt'",
            privileged=True
        )
        
        self.save()
class ChallengeSubmission(models.Model):
    """Soumission d'un défi avec vérification avancée"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    submitted_flag = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    submission_time = models.DateTimeField(auto_now_add=True)
    logs = models.TextField(blank=True)

    class Meta:
        ordering = ['-submission_time']
    
    def validate_submission(self):
        """Valide le flag selon le type de défi"""
        challenge_type = self.challenge.challenge_type.slug
        
        if challenge_type == 'ssh':
            self._validate_ssh()
        elif challenge_type == 'web':
            self._validate_web()
        # ... autres méthodes de validation
        
        self.save()
    
    def _validate_ssh(self):
        instance = UserChallengeInstance.objects.get(
            user=self.user,
            challenge=self.challenge
        )
        self.is_correct = (self.submitted_flag == instance.unique_flag)
    
    def _validate_web(self):
        # Exemple: Vérification via requête HTTP
        # à implémenter avec des appels API
        pass

# === Modèles utilitaires ===
class SSHKey(models.Model):
    """Clés SSH générées pour les instances utilisateur"""
    user_instance = models.OneToOneField(UserChallengeInstance, on_delete=models.CASCADE)
    private_key = models.TextField()
    public_key = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class ChallengeCategory(models.Model):
    """Catégorisation des défis"""
    challenges = models.ManyToManyField(Challenge)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name