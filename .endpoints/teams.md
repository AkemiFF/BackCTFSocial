### Teams

- `GET /api/teams/` - Liste toutes les équipes
- `POST /api/teams/` - Crée une nouvelle équipe
- `GET /api/teams/{slug}/` - Détails d'une équipe
- `PUT/PATCH /api/teams/{slug}/` - Modifie une équipe (admin/propriétaire seulement)
- `DELETE /api/teams/{slug}/` - Supprime une équipe (propriétaire seulement)
- `GET /api/teams/{slug}/members/` - Liste les membres d'une équipe
- `GET /api/teams/{slug}/projects/` - Liste les projets d'une équipe
- `GET /api/teams/{slug}/announcements/` - Liste les annonces d'une équipe
- `POST /api/teams/{slug}/join/` - Rejoint une équipe publique
- `POST /api/teams/{slug}/leave/` - Quitte une équipe

### Team Members

- `GET /api/teams/members/` - Liste les membres des équipes
- `GET /api/teams/members/{id}/` - Détails d'un membre
- `POST /api/teams/members/{id}/change_role/` - Change le rôle d'un membre (admin seulement)
- `POST /api/teams/members/{id}/remove/` - Retire un membre de l'équipe (admin seulement)

### Team Invitations

- `GET /api/teams/invitations/` - Liste les invitations
- `POST /api/teams/invitations/` - Crée une nouvelle invitation
- `GET /api/teams/invitations/{id}/` - Détails d'une invitation
- `DELETE /api/teams/invitations/{id}/` - Supprime une invitation
- `POST /api/teams/invitations/{id}/accept/` - Accepte une invitation
- `POST /api/teams/invitations/{id}/decline/` - Décline une invitation
- `GET /api/teams/invitations/received/` - Liste les invitations reçues
- `GET /api/teams/invitations/sent/` - Liste les invitations envoyées

### Team Projects

- `GET /api/teams/projects/` - Liste tous les projets
- `POST /api/teams/projects/` - Crée un nouveau projet
- `GET /api/teams/projects/{slug}/` - Détails d'un projet
- `PUT/PATCH /api/teams/projects/{slug}/` - Modifie un projet (admin seulement)
- `DELETE /api/teams/projects/{slug}/` - Supprime un projet (admin seulement)
- `GET /api/teams/projects/{slug}/tasks/` - Liste les tâches d'un projet
- `GET /api/teams/{team_slug}/projects/` - Liste les projets d'une équipe spécifique

### Team Tasks

- `GET /api/teams/tasks/` - Liste toutes les tâches
- `POST /api/teams/tasks/` - Crée une nouvelle tâche
- `GET /api/teams/tasks/{id}/` - Détails d'une tâche
- `PUT/PATCH /api/teams/tasks/{id}/` - Modifie une tâche
- `DELETE /api/teams/tasks/{id}/` - Supprime une tâche
- `POST /api/teams/tasks/{id}/change_status/` - Change le statut d'une tâche
- `POST /api/teams/tasks/{id}/assign/` - Assigne une tâche à un membre
- `GET /api/teams/{team_slug}/projects/{project_slug}/tasks/` - Liste les tâches d'un projet spécifique

### Team Announcements

- `GET /api/teams/announcements/` - Liste toutes les annonces
- `POST /api/teams/announcements/` - Crée une nouvelle annonce
- `GET /api/teams/announcements/{id}/` - Détails d'une annonce
- `PUT/PATCH /api/teams/announcements/{id}/` - Modifie une annonce (admin seulement)
- `DELETE /api/teams/announcements/{id}/` - Supprime une annonce (admin seulement)
- `POST /api/teams/announcements/{id}/toggle_pin/` - Épingle/désépingle une annonce
- `GET /api/teams/{team_slug}/announcements/` - Liste les annonces d'une équipe spécifique

## Fonctionnalités Clés

Ces endpoints offrent les fonctionnalités suivantes :

1. **Gestion des équipes**
    - Création et gestion d'équipes
    - Contrôle de la visibilité (public/privé)
    - Gestion des membres et des rôles (propriétaire, admin, membre)

2. **Système d'invitation**
    - Invitation de nouveaux membres
    - Acceptation/refus des invitations
    - Expiration automatique des invitations

3. **Projets d'équipe**
    - Création et gestion de projets
    - Suivi de l'état d'avancement
    - Contrôle de la visibilité (public/privé)

4. **Gestion des tâches**
    - Création et assignation de tâches
    - Priorisation et suivi de l'état
    - Estimation du temps nécessaire

5. **Communication interne**
    - Annonces d'équipe
    - Épinglage des annonces importantes

6. **Contrôle d'accès**
    - Permissions basées sur les rôles
    - Restrictions pour les actions sensibles
    - Visibilité adaptée selon le statut de membre
