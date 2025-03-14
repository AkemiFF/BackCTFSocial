#

## Notifi

### Notifications

- `GET /api/notifications/notifications/` - Liste toutes les notifications
- `POST /api/notifications/notifications/` - Crée une nouvelle notification
- `GET /api/notifications/notifications/{id}/` - Détails d'une notification
- `PUT/PATCH /api/notifications/notifications/{id}/` - Modifie une notification
- `DELETE /api/notifications/notifications/{id}/` - Supprime une notification
- `POST /api/notifications/notifications/{id}/mark_as_read/` - Marque une notification comme lue
- `POST /api/notifications/notifications/{id}/mark_as_unread/` - Marque une notification comme non lue
- `POST /api/notifications/notifications/mark_all_as_read/` - Marque toutes les notifications comme lues
- `GET /api/notifications/notifications/unread_count/` - Compte les notifications non lues
- `GET /api/notifications/notifications/my_notifications/` - Liste les notifications de l'utilisateur courant
- `DELETE /api/notifications/notifications/delete_all_read/` - Supprime toutes les notifications lues

### Notification Preferences

- `GET /api/notifications/preferences/` - Liste toutes les préférences de notification
- `POST /api/notifications/preferences/` - Crée une nouvelle préférence de notification
- `GET /api/notifications/preferences/{id}/` - Détails d'une préférence de notification
- `PUT/PATCH /api/notifications/preferences/{id}/` - Modifie une préférence de notification
- `DELETE /api/notifications/preferences/{id}/` - Supprime une préférence de notification
- `GET /api/notifications/preferences/my_preferences/` - Liste les préférences de l'utilisateur courant
- `POST /api/notifications/preferences/update_preferences/` - Met à jour plusieurs préférences à la fois
- `POST /api/notifications/preferences/toggle_all/` - Active/désactive toutes les préférences d'un type

## Fonctionnalités Clés

Ces endpoints offrent les fonctionnalités suivantes :

### Gestion des notifications

1. Création et envoi de notifications
2. Marquage des notifications comme lues/non lues
3. Suppression des notifications lues
4. Filtrage des notifications par type

### Préférences de notification

1. Configuration des préférences par type de notification
2. Activation/désactivation des notifications par canal (email, push, in-app)
3. Mise à jour groupée des préférences

### Comptage et suivi

1. Comptage des notifications non lues
2. Historique des notifications
3. Pagination et filtrage des résultats

### Contrôle d'accès

1. Permissions basées sur le destinataire
2. Restrictions pour les actions sensibles
3. Accès administrateur pour la gestion globale

Ces endpoints fournissent une API complète pour les fonctionnalités de notification de votre plateforme Hackitech, permettant aux utilisateurs de rester informés des activités pertinentes et de gérer leurs préférences de notification.

## Utilisation avec WebSockets (Optionnel)

Pour une expérience utilisateur optimale, vous pourriez envisager d'intégrer ces endpoints avec une solution WebSocket comme Django Channels pour des notifications en temps réel. Cela permettrait aux utilisateurs de recevoir des notifications instantanées sans avoir à rafraîchir la page.

Voici comment vous pourriez structurer cette intégration :

1. Installer Django Channels et configurer les consommateurs WebSocket
2. Créer un service de notification qui envoie des messages via WebSocket lorsqu'une nouvelle notification est créée
3. Mettre à jour le frontend pour se connecter au WebSocket et afficher les notifications en temps réel
