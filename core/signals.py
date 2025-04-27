# skills/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils.text import slugify

from accounts.models import Skill


@receiver(post_migrate)
def create_initial_skills(sender, **kwargs):
    if sender.name == 'core':  # Remplacez 'skills' par le nom de votre app
        if not Skill.objects.exists():
            skills_data = [
                # Langages de programmation
                {
                    "name": "Python",
                    "skill_type": "language",
                    "description": "Langage de programmation interprété orienté objet",
                    "icon": "fa-brands fa-python"
                },
                {
                    "name": "JavaScript",
                    "skill_type": "language",
                    "description": "Langage de script orienté objet principalement utilisé côté client",
                    "icon": "fa-brands fa-js"
                },
                # Frameworks
                {
                    "name": "Django",
                    "skill_type": "framework",
                    "parent": "Python",
                    "description": "Framework web Python haut niveau",
                    "icon": "fa-brands fa-python"
                },
                {
                    "name": "React",
                    "skill_type": "framework",
                    "parent": "JavaScript",
                    "description": "Bibliothèque JavaScript pour construire des interfaces utilisateur",
                    "icon": "fa-brands fa-react"
                },
                # Outils DevOps
                {
                    "name": "Docker",
                    "skill_type": "tool",
                    "description": "Plateforme de conteneurisation d'applications",
                    "icon": "fa-brands fa-docker"
                },
                {
                    "name": "Kubernetes",
                    "skill_type": "tool",
                    "description": "Système d'orchestration de conteneurs",
                    "related_skills": ["Docker"],
                    "icon": "fa-brands fa-docker"
                },
                # Méthodologies
                {
                    "name": "Agile",
                    "skill_type": "methodology",
                    "description": "Méthode de gestion de projet itérative",
                    "icon": "fa-solid fa-arrows-rotate"
                },
                # Compétences transversales
                {
                    "name": "Git",
                    "skill_type": "tool",
                    "description": "Système de contrôle de version distribué",
                    "icon": "fa-brands fa-git-alt"
                },
                {
                    "name": "SQL",
                    "skill_type": "technical",
                    "description": "Langage de gestion de bases de données relationnelles",
                    "icon": "fa-solid fa-database"
                }
            ]

            skills_cache = {}
            
            # Création des compétences de base
            for data in skills_data:
                parent = None
                if 'parent' in data:
                    parent = skills_cache.get(data['parent'])
                    del data['parent']
                
                related_skills = data.pop('related_skills', [])
                
                skill, created = Skill.objects.get_or_create(
                    name=data['name'],
                    defaults={
                        'slug': slugify(data['name']),
                        'skill_type': data['skill_type'],
                        'description': data.get('description', ''),
                        'icon': data.get('icon', ''),
                        'parent': parent
                    }
                )
                skills_cache[data['name']] = skill
                
                # Ajout des relations
                if related_skills:
                    for related_name in related_skills:
                        related_skill = skills_cache.get(related_name)
                        if related_skill:
                            skill.related_skills.add(related_skill)

            # Compétences supplémentaires
            advanced_skills = [
                ("Machine Learning", "technical", "Python", []),  # Ajout d'une liste vide pour 'related'
                ("Cybersécurité", "technical", None, []),         # Ajout de None et d'une liste vide
                ("DevOps", "methodology", None, ["Docker", "Kubernetes"]),
                ("CI/CD", "methodology", None, []),               # Ajout de None et d'une liste vide
                ("Test Driven Development", "methodology", None, [])  # Ajout de None et d'une liste vide
            ]

            for (name, skill_type, parent, related) in advanced_skills:
                parent_obj = skills_cache.get(parent) if parent else None
                skill, _ = Skill.objects.get_or_create(
                    name=name,
                    defaults={
                        'slug': slugify(name),
                        'skill_type': skill_type,
                        'parent': parent_obj
                    }
                )
                for rel in related:
                    if rel in skills_cache:
                        skill.related_skills.add(skills_cache[rel])