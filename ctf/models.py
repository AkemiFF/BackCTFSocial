import json
import logging
import os
import random
import shlex
import string
import subprocess
import tempfile
import time
import uuid
from uuid import UUID

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
    docker_context = models.JSONField(_('contexte Docker'), default=dict, blank=True,null=True)
    built_image = models.CharField(_('image construite'), max_length=255, blank=True)
    setup_ssh = models.BooleanField(_('setup SSH'), default=False)
    
    def build_docker_image(self):
        """Construit l'image Docker dynamiquement"""
        if not self.id:
            raise ValueError("L'objet Challenge doit être enregistré avant de construire l'image Docker.")
        
        client = docker_manager.client 
        image_tag = f"hackitech/{self.id}:latest"
        
        with tempfile.TemporaryDirectory() as context_dir:
            # Générer le Dockerfile
            if self.dockerfile:
                dockerfile_content = self.dockerfile 
            else:
                dockerfile_content = self.generate_default_dockerfile()
            logger.info(dockerfile_content)
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
            
    def generate_default_dockerfile(self):
        # if self.challenge_type.slug == 'ssh':
        #     return """
        #     FROM alpine:latest
            
        #     RUN apk add --no-cache openssh-server shadow && \
        #         adduser -D -h /home/ctf_user -s /bin/sh ctf_user && \      
        #         ssh-keygen -A && \
        #         sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config && \
        #         sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config && \
        #         sed -i 's/AllowTcpForwarding no/AllowTcpForwarding yes/' /etc/ssh/sshd_config && \
        #         sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config && \
        #         echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config && \
        #         mkdir -p /var/run/sshd && \
        #         chown -R ctf_user:ctf_user /home/ctf_user

        #     EXPOSE 22
        #     CMD ["sh", "-c", "which sshd && /usr/sbin/sshd -D -e"]
        #     """
        print(self.challenge_type.slug)
        if self.challenge_type.slug == 'ssh':
            data = """
                FROM alpine:latest

                RUN apk add --no-cache openssh-server shadow && \
                    ssh-keygen -A && \
                    mkdir -p /var/run/sshd 

                EXPOSE 22
                CMD ["/usr/sbin/sshd", "-D", "-e"]
                """
            print(data)
            return data

        elif self.challenge_type.slug == 'web':
            data = """
            FROM nginx:alpine
            CMD ["nginx", "-g", "daemon off;"]  # Main process
            """
            print(data)
            return data
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
        ('starting', 'Démarrage'),
        ('failed', 'Échec'),
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
    

    def generate_encrypted_flag(self):
        # 1. Génération du flag aléatoire
        flag = f'thisWasEasy{{{"".join(random.choices(string.ascii_uppercase + string.digits, k=16))}}}'
        self.unique_flag = flag

        # 2. Chiffrement du flag
        #    - pas de salt pour sortir une donnée chiffrée reproductible
        #    - -p pour afficher key & iv (sur stderr), très pratique pour apprendre à décrypter
        cmd = (
            "echo -n {flag_esc} | "
            "openssl enc -aes-128-cbc -a -nosalt -pass pass:beginner -p"
        ).format(flag_esc=shlex.quote(flag))

        # On récupère stdout+stderr (output chiffré + key/iv)
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        encrypted_flag_with_params = result.decode().strip()

        # Si tu veux isoler juste la partie base64 (sans key/iv), tu peux faire :
        # encrypted_flag = encrypted_flag_with_params.splitlines()[-1]

        return encrypted_flag_with_params

    def save(self, *args, **kwargs):
        if not self.expiry_time:
            self.expiry_time = timezone.now() + timezone.timedelta(hours=2)
        super().save(*args, **kwargs)
    
    
    def connection_info(self):
        """Retourne les infos de connexion selon le type de défi"""
        if self.challenge.challenge_type.slug == 'ssh':
            port = self.assigned_ports.get('22/tcp')
            if not port:
                logger.warning("Aucun port SSH assigné pour cette instance")
                return {}
            
            return {
                'host': settings.DOCKER_HOST_IP,
                'port': port,
                'username': 'ctf_user',
                'auth_method': 'ssh_key'
            }
        elif self.challenge.challenge_type.slug == 'web':
            return {'url': self.web_url}
        return {}
    
    def start_container(self):
        """Lance le conteneur Docker (version asynchrone)"""
        try:
            container = docker_manager.client.containers.run(
                image=self.challenge.built_image,
                detach=True,
                network_mode=docker_manager.network_name,
                name=f"{self.user.id}_{self.challenge.id}_{uuid.uuid4().hex[:8]}",
                ports=self._get_port_bindings(),
                environment={**self._get_environment_vars(), 'SSHD_OPTS': '-D -e'},
                labels={
                    'hackitech_user': str(self.user.id),
                    'hackitech_challenge': str(self.challenge.id)
                }
            )
            container.reload()

            # Mise à jour minimale immédiate
            self.container_id = container.id
            logger.info(f"Conteneur {container} ")
            logger.info(f"Ports assignés par Docker : {container.ports}")        
            self.assigned_ports = self._sanitize_ports(container.ports)
            
            
            
            self.save()
            self._post_start_setup(container) 
            
            if not self.challenge.setup_ssh:
                self.status = 'running'
                self.save()
                return
                
            logger.info(f"Conteneur {container.id} lancé avec succès (statut: {container.status})")

        except docker.errors.APIError as e:
            logger.error(f"Erreur Docker API: {str(e)}")
            self.status = 'failed'
            self.save()
            raise
        
        except Exception as e:
            logger.error(f"Erreur inattendue: {str(e)}")
            self.status = 'failed'
            self.save()
            raise
            
    def _sanitize_ports(self, docker_ports):
        sanitized = {}
        if docker_ports:
            for container_port, host_configs in docker_ports.items():
                logger.debug(f"Port {container_port} : {host_configs}")
                if host_configs:
                    sanitized[container_port] = host_configs[0]['HostPort']
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
        """Retourne les bindings de ports au format Docker SDK"""
        port_bindings = {}
        for container_port, host_port in self.challenge.docker_ports.items():
            logger.info(f"Port {container_port} : {host_port}")
            # Format attendu: {container_port: [host_port]} ou [] pour aléatoire
            port_bindings[container_port] = str(host_port) if host_port is not None else None
            logger.info(f"Port bindings : {port_bindings}")
        return port_bindings

    def _post_start_setup(self, container):
        """Configuration post-démarrage"""
        if self.challenge.challenge_type.slug == 'ssh':
            self._setup_ssh_access(container)
        elif self.challenge.challenge_type.slug == 'web':
            self._setup_web_access(container)

    def _setup_ssh_access(self, container):
        if not self.challenge.setup_ssh : 
            return
        
        if container.status != 'running':
            container.start()
            time.sleep(2)
        
        
        logger.info(f"asigned port : {self.assigned_ports}")
        
        if '22/tcp' not in self.assigned_ports:
            logger.error("Aucun port SSH (22/tcp) n'a été assigné au conteneur")
            raise ValueError("Port SSH manquant")
        
        private_key, public_key = generate_ssh_keys()

        exit_code, output = container.exec_run("test -f /etc/ssh/sshd_config", user="root")
        if exit_code != 0:
            logger.error("Le fichier /etc/ssh/sshd_config n'existe pas. Réinstallation d'OpenSSH...")
            exit_code, output = container.exec_run("apk add --no-cache openssh-server", user="root")
            if exit_code != 0:
                logger.error(f"Échec de la réinstallation d'OpenSSH : {output.decode()}")
                raise RuntimeError("Échec de la réinstallation d'OpenSSH")
            
            # Générez le fichier de configuration SSH
            exit_code, output = container.exec_run("ssh-keygen -A", user="root")
            if exit_code != 0:
                logger.error(f"Échec de la génération des clés SSH : {output.decode()}")
                raise RuntimeError("Échec de la génération des clés SSH")
        logger.info(f"Challenge ID: {self.challenge.id}, Challenge Name: {self.challenge.title}")

        target = UUID("16a1c409-840b-4edf-8c2c-2a0bbce4d61a")
        if self.challenge.id == target:
            encrypted_flag = self.generate_encrypted_flag()
            print(encrypted_flag)
            cmd1 = (
                "sh -c '"
                "id -u ctf_user || adduser -D -h /home/ctf_user -s /bin/sh ctf_user && "
                "mkdir -p /home/ctf_user/.ssh && "
                "echo \"{public_key}\" > /home/ctf_user/.ssh/authorized_keys && "
                "chown -R ctf_user:ctf_user /home/ctf_user && "
                "chmod 700 /home/ctf_user/.ssh && "
                "chmod 600 /home/ctf_user/.ssh/authorized_keys &&"
                "touch /home/ctf_user/just_ignore_me && "                
                f"echo \"{encrypted_flag}\" > /home/ctf_user/just_ignore_me && "
                "chown ctf_user:ctf_user /home/ctf_user/just_ignore_me'"
            ).format(public_key=public_key, encrypted_flag=encrypted_flag)
        else:
            cmd1 = (
                "sh -c '"
                "id -u ctf_user || adduser -D -h /home/ctf_user -s /bin/sh ctf_user && "
                "mkdir -p /home/ctf_user/.ssh && "
                "echo \"{public_key}\" > /home/ctf_user/.ssh/authorized_keys && "
                "chown -R ctf_user:ctf_user /home/ctf_user && "
                "chmod 700 /home/ctf_user/.ssh && "
                "chmod 600 /home/ctf_user/.ssh/authorized_keys'"
            ).format(public_key=public_key)


        exit_code, output = container.exec_run(cmd1, user="root")
        if exit_code != 0:
            logger.error(f"Erreur lors de la configuration de base SSH : {output.decode()}")
            raise RuntimeError(f"Échec configuration SSH : {output.decode()}")
        else:
            logger.info("Configuration de base SSH réussie.")

        # Partie 2 : Modification de /etc/ssh/sshd_config pour PasswordAuthentication
        cmd2 = (
            "sh -c '"
            "sed -i \"s/#PasswordAuthentication yes/PasswordAuthentication no/\" /etc/ssh/sshd_config'"
        )
        exit_code, output = container.exec_run(cmd2, user="root")
        if exit_code != 0:
            logger.error(f"Erreur sur PasswordAuthentication : {output.decode()}")
        else:
            logger.info("Modification de PasswordAuthentication réussie.")

        # Partie 3 : Modification de /etc/ssh/sshd_config pour PermitRootLogin
        cmd3 = (
            "sh -c '"
            "sed -i \"s/#PermitRootLogin prohibit-password/PermitRootLogin no/\" /etc/ssh/sshd_config'"
        )
        exit_code, output = container.exec_run(cmd3, user="root")
        if exit_code != 0:
            logger.error(f"Erreur sur PermitRootLogin : {output.decode()}")
        else:
            logger.info("Modification de PermitRootLogin réussie.")

        # Partie 4 : Modification de /etc/ssh/sshd_config pour AllowTcpForwarding
        cmd4 = (
            "sh -c '"
            "sed -i \"s/AllowTcpForwarding no/AllowTcpForwarding yes/\" /etc/ssh/sshd_config'"
        )
        exit_code, output = container.exec_run(cmd4, user="root")
        if exit_code != 0:
            logger.error(f"Erreur sur AllowTcpForwarding : {output.decode()}")
        else:
            logger.info("Modification de AllowTcpForwarding réussie.")

        # Partie 5 : Modification de /etc/ssh/sshd_config pour PubkeyAuthentication
        cmd5 = (
            "sh -c '"
            "sed -i \"s/#PubkeyAuthentication yes/PubkeyAuthentication yes/\" /etc/ssh/sshd_config && "
            "echo \"PubkeyAuthentication yes\" >> /etc/ssh/sshd_config'"
        )
        exit_code, output = container.exec_run(cmd5, user="root")
        if exit_code != 0:
            logger.error(f"Erreur sur PubkeyAuthentication : {output.decode()}")
        else:
            logger.info("Modification de PubkeyAuthentication réussie.")

        # Partie 6 : Modification de /etc/shadow pour corriger la ligne de l'utilisateur
        cmd6 = (
            "sh -c '"
            "sed -i \"s/^ctf_user:!:/ctf_user::/\" /etc/shadow'"
        )
        exit_code, output = container.exec_run(cmd6, user="root")
        if exit_code != 0:
            logger.error(f"Erreur sur la modification de /etc/shadow : {output.decode()}")
        else:
            logger.info("Modification de /etc/shadow réussie.")
        SSHKey.objects.create(
            user_instance=self,
            private_key=private_key,
            public_key=public_key
        )
        
        # encryptor = get_crypt()
        self.ssh_credentials = {
            'port': self.assigned_ports['22/tcp'],
            'username': 'ctf_user',
            'key': private_key
        }
        self.status = 'running'
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='challenge_submissions')    
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
        print(instance.unique_flag)
        if (self.is_correct) :
            self.user.update_points(self.challenge.points)
    
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