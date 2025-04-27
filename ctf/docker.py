# core/docker.py
import logging

import docker
from django.conf import settings

logger = logging.getLogger(__name__)

class DockerManager:
    def __init__(self):
        self.client = docker.from_env()
        self.network_name = settings.DOCKER_NETWORK or 'hackitech_network'
        self.ensure_network()
                
    def ensure_network(self):
            try:
                network = self.client.networks.get(self.network_name)
                
                # Vérifier si le réseau a des conteneurs attachés
                if network.attrs['Containers']:
                    # logger.warning(f"Le réseau {self.network_name} a des conteneurs actifs. Aucune modification.")
                    return
                
                # Supprimer uniquement si la configuration IPAM est incorrecte
                if not network.attrs['IPAM']['Config']:
                    network.remove()
                    raise docker.errors.NotFound
                
            except docker.errors.NotFound:
                # Créer le réseau avec une configuration sécurisée
                ipam_pool = docker.types.IPAMPool(
                    subnet="172.30.0.0/24",
                    gateway="172.30.0.1"
                )
                self.client.networks.create(
                    self.network_name,
                    driver="bridge",
                    ipam=docker.types.IPAMConfig(pool_configs=[ipam_pool]),
                    options={
                        "com.docker.network.bridge.enable_icc": "true",
                        "com.docker.network.bridge.name": self.network_name
                    }
                )
                logger.info(f"Réseau {self.network_name} créé avec succès.")
                
                
docker_manager = DockerManager()