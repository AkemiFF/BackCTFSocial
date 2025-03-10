#

## social

### Posts

- `GET /api/social/posts/` - Liste toutes les publications
- `POST /api/social/posts/` - Crée une nouvelle publication
- `GET /api/social/posts/{id}/` - Détails d'une publication
- `PUT/PATCH /api/social/posts/{id}/` - Modifie une publication (propriétaire seulement)
- `DELETE /api/social/posts/{id}/` - Supprime une publication (propriétaire seulement)
- `POST /api/social/posts/{id}/like/` - Aime une publication
- `POST /api/social/posts/{id}/unlike/` - Retire le like d'une publication
- `POST /api/social/posts/{id}/save/` - Sauvegarde une publication
- `POST /api/social/posts/{id}/unsave/` - Retire la sauvegarde d'une publication
- `POST /api/social/posts/{id}/share/` - Partage une publication
- `POST /api/social/posts/{id}/report/` - Signale une publication
- `GET /api/social/posts/{id}/comments/` - Liste les commentaires d'une publication
- `GET /api/social/posts/feed/` - Flux d'actualités de l'utilisateur
- `GET /api/social/posts/saved/` - Publications sauvegardées par l'utilisateur

### Comments

- `GET /api/social/comments/` - Liste tous les commentaires
- `POST /api/social/comments/` - Crée un nouveau commentaire
- `GET /api/social/comments/{id}/` - Détails d'un commentaire
- `PUT/PATCH /api/social/comments/{id}/` - Modifie un commentaire (propriétaire seulement)
- `DELETE /api/social/comments/{id}/` - Supprime un commentaire (propriétaire seulement)
- `POST /api/social/comments/{id}/like/` - Aime un commentaire
- `POST /api/social/comments/{id}/unlike/` - Retire le like d'un commentaire
- `POST /api/social/comments/{id}/report/` - Signale un commentaire
- `GET /api/social/comments/{id}/replies/` - Liste les réponses à un commentaire

### Conversations

- `GET /api/social/conversations/` - Liste les conversations de l'utilisateur
- `POST /api/social/conversations/` - Crée une nouvelle conversation
- `GET /api/social/conversations/{id}/` - Détails d'une conversation
- `PUT/PATCH /api/social/conversations/{id}/` - Modifie une conversation (participants seulement)
- `DELETE /api/social/conversations/{id}/` - Supprime une conversation (participants seulement)
- `GET /api/social/conversations/{id}/messages/` - Liste les messages d'une conversation
- `POST /api/social/conversations/{id}/add_participant/` - Ajoute un participant à une conversation
- `POST /api/social/conversations/{id}/remove_participant/` - Retire un participant d'une conversation
- `POST /api/social/conversations/{id}/leave/` - Quitte une conversation

### Messages

- `GET /api/social/messages/` - Liste les messages de l'utilisateur
- `POST /api/social/messages/` - Envoie un nouveau message
- `GET /api/social/messages/{id}/` - Détails d'un message
- `PUT/PATCH /api/social/messages/{id}/` - Modifie un message (expéditeur seulement)
- `DELETE /api/social/messages/{id}/` - Supprime un message (expéditeur seulement)
- `POST /api/social/messages/{id}/mark_read/` - Marque un message comme lu
- `POST /api/social/messages/mark_conversation_read/` - Marque tous les messages d'une conversation comme lus

### Projects

- `GET /api/social/projects/` - Liste tous les projets
- `POST /api/social/projects/` - Crée un nouveau projet
- `GET /api/social/projects/{id}/` - Détails d'un projet
- `PUT/PATCH /api/social/projects/{id}/` - Modifie un projet (propriétaire seulement)
- `DELETE /api/social/projects/{id}/` - Supprime un projet (propriétaire seulement)

### Social Interactions

- `GET /api/social/interactions/` - Liste les interactions de l'utilisateur
- `POST /api/social/interactions/` - Crée une nouvelle interaction
- `GET /api/social/interactions/{id}/` - Détails d'une interaction
- `DELETE /api/social/interactions/{id}/` - Supprime une interaction (propriétaire seulement)

## Fonctionnalités Clés

Ces endpoints offrent les fonctionnalités suivantes :

1. **Publications et commentaires**
    - Création, modification et suppression de publications et commentaires
    - Support pour différents types de contenu (texte, image, code, lien)
    - Système de commentaires hiérarchique (réponses aux commentaires)

2. **Interactions sociales**
    - Likes, partages et signalements
    - Sauvegarde de publications pour consultation ultérieure
    - Flux d'actualités personnalisé

3. **Messagerie privée**
    - Conversations individuelles et de groupe
    - Support pour différents types de messages (texte, image, fichier, code)
    - Gestion des participants
    - Suivi des messages lus/non lus

4. **Projets**
    - Présentation des projets des utilisateurs
    - Association avec des technologies (compétences)
    - Contrôle de la visibilité (public/privé)

5. **Contrôle d'accès**
    - Restrictions basées sur la propriété du contenu
    - Gestion de la visibilité (contenu public/privé)
    - Permissions spéciales pour les administrateurs
