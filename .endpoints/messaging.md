### Channels

- `GET /api/messaging/channels/` - Liste tous les canaux de l'utilisateur
- `POST /api/messaging/channels/` - Crée un nouveau canal
- `GET /api/messaging/channels/{id}/` - Détails d'un canal
- `PUT/PATCH /api/messaging/channels/{id}/` - Modifie un canal (admin seulement)
- `DELETE /api/messaging/channels/{id}/` - Supprime un canal (admin seulement)
- `GET /api/messaging/channels/{id}/messages/` - Liste les messages d'un canal
- `POST /api/messaging/channels/{id}/mark_as_read/` - Marque tous les messages d'un canal comme lus
- `POST /api/messaging/channels/{id}/add_member/` - Ajoute un membre à un canal
- `POST /api/messaging/channels/{id}/remove_member/` - Retire un membre d'un canal
- `POST /api/messaging/channels/{id}/leave/` - Quitte un canal
- `GET /api/messaging/channels/direct/?user_id={id}` - Obtient ou crée un canal de message direct avec un utilisateur

### Channel Members

- `GET /api/messaging/members/` - Liste les membres des canaux de l'utilisateur
- `GET /api/messaging/members/{id}/` - Détails d'un membre
- `POST /api/messaging/members/{id}/change_role/` - Change le rôle d'un membre (admin seulement)
- `POST /api/messaging/members/{id}/toggle_mute/` - Active/désactive la mise en sourdine d'un canal

### Messages

- `GET /api/messaging/messages/` - Liste les messages des canaux de l'utilisateur
- `POST /api/messaging/messages/` - Envoie un nouveau message
- `GET /api/messaging/messages/{id}/` - Détails d'un message
- `PUT/PATCH /api/messaging/messages/{id}/` - Modifie un message (expéditeur seulement)
- `DELETE /api/messaging/messages/{id}/` - Supprime un message (expéditeur seulement)
- `POST /api/messaging/messages/{id}/mark_read/` - Marque un message comme lu
- `POST /api/messaging/messages/mark_channel_read/` - Marque tous les messages d'un canal comme lus

### Read Receipts

- `GET /api/messaging/read-receipts/` - Liste les accusés de lecture
- `GET /api/messaging/read-receipts/{id}/` - Détails d'un accusé de lecture

### Attachments

- `GET /api/messaging/attachments/` - Liste les pièces jointes
- `GET /api/messaging/attachments/{id}/` - Détails d'une pièce jointe

## Fonctionnalités Clés

Ces endpoints offrent les fonctionnalités suivantes :

1. **Canaux de messagerie**
    - Canaux de groupe et messages directs
    - Gestion des membres et des rôles (admin, membre)
    - Contrôle d'accès basé sur l'appartenance au canal

2. **Messagerie en temps réel**
    - Envoi et réception de messages
    - Support pour différents types de messages (texte, image, fichier, code, système)
    - Réponses aux messages

3. **Gestion des pièces jointes**
    - Support pour différents types de fichiers (images, documents, audio, vidéo)
    - Stockage et récupération des pièces jointes

4. **Accusés de lecture**
    - Suivi des messages lus par chaque utilisateur
    - Comptage des messages non lus
    - Marquage des messages comme lus

5. **Notifications et préférences**
    - Mise en sourdine des canaux
    - Dernière activité des utilisateurs
