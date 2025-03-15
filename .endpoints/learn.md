#

## Learn

### Cours

- `GET /api/courses/` - Liste de tous les cours avec filtrage et tri
- `GET /api/courses/{id}/` - Détails d'un cours spécifique
- `GET /api/courses/categories/` - Liste des catégories de cours
- `GET /api/courses/tags/` - Liste des tags de cours
- `GET /api/courses/{id}/modules/` - Liste des modules d'un cours

### Modules

- `GET /api/modules/{id}/` - Détails d'un module spécifique
- `GET /api/modules/{id}/content/` - Contenu d'un module spécifique
- `GET /api/modules/{id}/quiz/` - Questions du quiz d'un module
- `POST /api/modules/{id}/submit_quiz/` - Soumettre les réponses d'un quiz
- `POST /api/modules/{id}/complete/` - Marquer un module comme complété

### Progression de l'Utilisateur

- `GET /api/user/progress/` - Progression de l'utilisateur pour tous les cours
- `GET /api/user/progress/course/?course_id={id}` - Progression pour un cours spécifique

### Certifications

- `GET /api/user/certifications/` - Liste des certifications de l'utilisateur
- `GET /api/user/certifications/{id}/` - Détails d'une certification spécifique

### Points et Niveau

- `GET /api/user/points/` - Points et niveau de l'utilisateur
- `GET /api/user/points/transactions/` - Historique des transactions de points

### Profil Utilisateur

- `GET /api/user/profile/` - Profil de l'utilisateur connecté

## Données de Référence

- `GET /api/admin/reference-data/` - Récupérer les données de référence pour les formulaires

### Gestion des Cours

- `GET /api/admin/courses/` - Liste de tous les cours
- `POST /api/admin/courses/` - Créer un nouveau cours
- `GET /api/admin/courses/{id}/` - Détails d'un cours
- `PUT /api/admin/courses/{id}/` - Mettre à jour un cours
- `DELETE /api/admin/courses/{id}/` - Supprimer un cours

### Gestion des Modules

- `GET /api/admin/modules/` - Liste de tous les modules
- `POST /api/admin/modules/` - Créer un nouveau module
- `GET /api/admin/modules/{id}/` - Détails d'un module
- `PUT /api/admin/modules/{id}/` - Mettre à jour un module
- `DELETE /api/admin/modules/{id}/` - Supprimer un module
- `POST /api/admin/modules/{id}/add_content/` - Ajouter un élément de contenu à un module
- `PUT /api/admin/modules/{id}/reorder_content/` - Réordonner les éléments de contenu d'un module

### Gestion des Éléments de Contenu

- `GET /api/admin/content-items/` - Liste de tous les éléments de contenu
- `POST /api/admin/content-items/` - Créer un nouvel élément de contenu
- `GET /api/admin/content-items/{id}/` - Détails d'un élément de contenu
- `PUT /api/admin/content-items/{id}/` - Mettre à jour un élément de contenu
- `DELETE /api/admin/content-items/{id}/` - Supprimer un élément de contenu
