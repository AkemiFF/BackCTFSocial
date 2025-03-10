# Learning

## endpoint

### Learning Paths

- `GET /api/learning/learning-paths/` - Liste tous les parcours d'apprentissage
- `POST /api/learning/learning-paths/` - Crée un nouveau parcours d'apprentissage (instructeurs seulement)
- `GET /api/learning/learning-paths/{slug}/` - Détails d'un parcours d'apprentissage
- `PUT/PATCH /api/learning/learning-paths/{slug}/` - Modifie un parcours d'apprentissage (instructeurs seulement)
- `DELETE /api/learning/learning-paths/{slug}/` - Supprime un parcours d'apprentissage (instructeurs seulement)
- `GET /api/learning/learning-paths/{slug}/enroll/` - S'inscrire à un parcours d'apprentissage
- `GET /api/learning/learning-paths/enrolled/` - Liste les parcours d'apprentissage auxquels l'utilisateur est inscrit

### Courses

- `GET /api/learning/courses/` - Liste tous les cours
- `POST /api/learning/courses/` - Crée un nouveau cours (instructeurs seulement)
- `GET /api/learning/courses/{slug}/` - Détails d'un cours
- `PUT/PATCH /api/learning/courses/{slug}/` - Modifie un cours (instructeurs seulement)
- `DELETE /api/learning/courses/{slug}/` - Supprime un cours (instructeurs seulement)
- `GET /api/learning/courses/{slug}/enroll/` - S'inscrire à un cours
- `GET /api/learning/courses/enrolled/` - Liste les cours auxquels l'utilisateur est inscrit

### Modules

- `GET /api/learning/modules/` - Liste tous les modules
- `POST /api/learning/modules/` - Crée un nouveau module (instructeurs seulement)
- `GET /api/learning/modules/{id}/` - Détails d'un module
- `PUT/PATCH /api/learning/modules/{id}/` - Modifie un module (instructeurs seulement)
- `DELETE /api/learning/modules/{id}/` - Supprime un module (instructeurs seulement)
- `POST /api/learning/modules/{id}/mark_completed/` - Marque un module comme terminé

### Quizzes

- `GET /api/learning/quizzes/` - Liste tous les quiz
- `POST /api/learning/quizzes/` - Crée un nouveau quiz (instructeurs seulement)
- `GET /api/learning/quizzes/{id}/` - Détails d'un quiz
- `PUT/PATCH /api/learning/quizzes/{id}/` - Modifie un quiz (instructeurs seulement)
- `DELETE /api/learning/quizzes/{id}/` - Supprime un quiz (instructeurs seulement)
- `POST /api/learning/quizzes/{id}/submit/` - Soumet les réponses à un quiz
- `GET /api/learning/quizzes/{id}/attempts/` - Liste les tentatives de l'utilisateur pour un quiz

### Questions

- `GET /api/learning/questions/` - Liste toutes les questions
- `POST /api/learning/questions/` - Crée une nouvelle question (instructeurs seulement)
- `GET /api/learning/questions/{id}/` - Détails d'une question
- `PUT/PATCH /api/learning/questions/{id}/` - Modifie une question (instructeurs seulement)
- `DELETE /api/learning/questions/{id}/` - Supprime une question (instructeurs seulement)

### Progression des utilisateurs

- `GET /api/learning/course-progress/` - Liste la progression de l'utilisateur dans les cours
- `GET /api/learning/module-progress/` - Liste la progression de l'utilisateur dans les modules
- `GET /api/learning/quiz-attempts/` - Liste les tentatives de quiz de l'utilisateur

## Fonctionnalités Clés

Ces endpoints offrent les fonctionnalités suivantes :

1. **Gestion des parcours d'apprentissage et des cours**
    - Création, modification et suppression de parcours d'apprentissage, cours, modules, quiz et questions
    - Filtrage et recherche avancés

2. **Inscription et progression**
    - Inscription aux parcours d'apprentissage et aux cours
    - Suivi de la progression des utilisateurs
    - Marquage des modules comme terminés

3. **Quiz et évaluation**
    - Soumission des réponses aux quiz
    - Calcul automatique des scores
    - Historique des tentatives

4. **Contrôle d'accès**
    - Restrictions basées sur les rôles (étudiant, mentor, administrateur)
    - Gestion des contenus nécessitant un abonnement
