#

## Core

### Tags

- `GET /api/core/tags/` - Liste tous les tags
- `POST /api/core/tags/` - Crée un nouveau tag (admins seulement)
- `GET /api/core/tags/{slug}/` - Détails d'un tag
- `PUT/PATCH /api/core/tags/{slug}/` - Modifie un tag (admins seulement)
- `DELETE /api/core/tags/{slug}/` - Supprime un tag (admins seulement)

### Categories

- `GET /api/core/categories/` - Liste toutes les catégories
- `POST /api/core/categories/` - Crée une nouvelle catégorie (admins seulement)
- `GET /api/core/categories/{slug}/` - Détails d'une catégorie
- `PUT/PATCH /api/core/categories/{slug}/` - Modifie une catégorie (admins seulement)
- `DELETE /api/core/categories/{slug}/` - Supprime une catégorie (admins seulement)
- `GET /api/core/categories/root/` - Liste les catégories racines (sans parent)
- `GET /api/core/categories/{slug}/children/` - Liste les sous-catégories d'une catégorie

### Skills

- `GET /api/core/skills/` - Liste toutes les compétences
- `POST /api/core/skills/` - Crée une nouvelle compétence (admins seulement)
- `GET /api/core/skills/{slug}/` - Détails d'une compétence
- `PUT/PATCH /api/core/skills/{slug}/` - Modifie une compétence (admins seulement)
- `DELETE /api/core/skills/{slug}/` - Supprime une compétence (admins seulement)
- `GET /api/core/skills/root/` - Liste les compétences racines (sans parent)
- `GET /api/core/skills/{slug}/children/` - Liste les sous-compétences d'une compétence
- `GET /api/core/skills/{slug}/related/` - Liste les compétences liées à une compétence

### Settings

- `GET /api/core/settings/` - Liste tous les paramètres (publics pour les utilisateurs, tous pour les admins)
- `POST /api/core/settings/` - Crée un nouveau paramètre (admins seulement)
- `GET /api/core/settings/{key}/` - Détails d'un paramètre
- `PUT/PATCH /api/core/settings/{key}/` - Modifie un paramètre (admins seulement)
- `DELETE /api/core/settings/{key}/` - Supprime un paramètre (admins seulement)

### Feedback

- `GET /api/core/feedback/` - Liste tous les feedbacks (les siens pour les utilisateurs, tous pour les admins)
- `POST /api/core/feedback/` - Crée un nouveau feedback
- `GET /api/core/feedback/{id}/` - Détails d'un feedback
- `PUT/PATCH /api/core/feedback/{id}/` - Modifie un feedback (propriétaire ou admins seulement)
- `DELETE /api/core/feedback/{id}/` - Supprime un feedback (propriétaire ou admins seulement)
- `POST /api/core/feedback/{id}/resolve/` - Marque un feedback comme résolu (admins seulement)

### Audit

- `GET /api/core/audit/` - Liste toutes les entrées d'audit (admins seulement)
- `GET /api/core/audit/{id}/` - Détails d'une entrée d'audit (admins seulement)
- `GET /api/core/audit/my_activity/` - Liste les activités de l'utilisateur courant

## Fonctionnalités Clés

Ces endpoints offrent les fonctionnalités suivantes :

1. **Gestion des taxonomies**
    - Tags pour la catégorisation du contenu
    - Catégories hiérarchiques pour l'organisation
    - Compétences avec relations parent-enfant et compétences liées

2. **Configuration du système**
    - Paramètres système avec contrôle de visibilité
    - Accès restreint aux administrateurs

3. **Feedback utilisateur**
    - Soumission de feedback (bugs, suggestions, etc.)
    - Suivi du statut des feedbacks
    - Résolution par les administrateurs

4. **Audit et sécurité**
    - Journal d'audit pour les actions importantes
    - Suivi de l'activité des utilisateurs
    - Accès restreint aux administrateurs
