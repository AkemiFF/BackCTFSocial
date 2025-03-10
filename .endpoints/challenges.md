#

## Challenges

- `GET /api/challenges/challenges/` - Liste tous les défis
- `POST /api/challenges/challenges/` - Crée un nouveau défi (créateurs seulement)
- `GET /api/challenges/challenges/{id}/` - Détails d'un défi
- `PUT/PATCH /api/challenges/challenges/{id}/` - Modifie un défi (créateurs seulement)
- `DELETE /api/challenges/challenges/{id}/` - Supprime un défi (créateurs seulement)
- `POST /api/challenges/challenges/{id}/submit_flag/` - Soumet un flag pour un défi
- `GET /api/challenges/challenges/{id}/hints/` - Liste les indices d'un défi
- `POST /api/challenges/challenges/{id}/unlock_hint/` - Débloque un indice
- `POST /api/challenges/challenges/{id}/rate/` - Évalue un défi
- `GET /api/challenges/challenges/completed/` - Liste les défis complétés par l'utilisateur

### Resources

- `GET /api/challenges/resources/` - Liste toutes les ressources
- `POST /api/challenges/resources/` - Crée une nouvelle ressource (créateurs seulement)
- `GET /api/challenges/resources/{id}/` - Détails d'une ressource
- `PUT/PATCH /api/challenges/resources/{id}/` - Modifie une ressource (créateurs seulement)
- `DELETE /api/challenges/resources/{id}/` - Supprime une ressource (créateurs seulement)

### Submissions

- `GET /api/challenges/submissions/` - Liste les soumissions de l'utilisateur
- `GET /api/challenges/submissions/{id}/` - Détails d'une soumission

### User Hints

- `GET /api/challenges/user-hints/` - Liste les indices débloqués par l'utilisateur
- `GET /api/challenges/user-hints/{id}/` - Détails d'un indice débloqué

### Ratings

- `GET /api/challenges/ratings/` - Liste les évaluations de l'utilisateur
- `POST /api/challenges/ratings/` - Crée une nouvelle évaluation
- `GET /api/challenges/ratings/{id}/` - Détails d'une évaluation
- `PUT/PATCH /api/challenges/ratings/{id}/` - Modifie une évaluation
- `DELETE /api/challenges/ratings/{id}/` - Supprime une évaluation

### Completions

- `GET /api/challenges/completions/` - Liste les défis complétés par l'utilisateur
- `GET /api/challenges/completions/{id}/` - Détails d'un défi complété

## 7. Fonctionnalités Clés

Ces endpoints offrent les fonctionnalités suivantes:

1. **Gestion des défis**

   1. Création, modification et suppression de défis et de ressources associées
   2. Filtrage et recherche avancés

2. **Soumission de flags**

   1. Vérification des flags soumis
   2. Attribution automatique de points
   3. Limitation du nombre de tentatives

3. **Système d'indices**

   1. Déblocage d'indices en échange de points
   2. Gestion des indices débloqués par l'utilisateur

4. **Évaluation et feedback**

   1. Notation des défis par les utilisateurs
   2. Collecte de feedback pour améliorer les défis

5. **Suivi de progression**

   1. Historique des soumissions
   2. Suivi des défis complétés

6. **Contrôle d'accès**

   1. Restrictions basées sur les rôles
   2. Gestion des défis nécessitant un abonnement
