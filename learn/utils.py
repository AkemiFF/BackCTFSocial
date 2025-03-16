import uuid
from django.db.models import Count
from .models import UserProgress, ModuleCompletion, Certification

def update_course_progress(user, course):
    """Mettre à jour la progression d'un utilisateur pour un cours"""
    total_modules = course.modules.count()
    if total_modules == 0:
        return
    
    completed_modules = ModuleCompletion.objects.filter(
        user=user,
        module__course=course
    ).count()
    
    progress = int((completed_modules / total_modules) * 100)
    
    # Mettre à jour ou créer l'entrée de progression
    user_progress, created = UserProgress.objects.get_or_create(
        user=user,
        course=course,
        defaults={'progress': progress}
    )
    
    if not created:
        user_progress.progress = progress
        user_progress.save()
    
    # Vérifier si le cours est complété pour délivrer une certification
    if progress == 100:
        issue_certification(user, course)

def issue_certification(user, course):
    """Délivrer une certification à un utilisateur pour un cours complété"""
    # Vérifier si l'utilisateur a déjà une certification pour ce cours
    if not Certification.objects.filter(user=user, course=course).exists():
        # Générer un ID unique pour le certificat
        certificate_id = f"CERT-{uuid.uuid4().hex[:8].upper()}"
        
        # Créer la certification
        Certification.objects.create(
            user=user,
            course=course,
            certificate_id=certificate_id
        )
        
        return True
    return False

def calculate_user_level(points):
    """Calculer le niveau de l'utilisateur en fonction de ses points"""
    if points < 100:
        return 1
    elif points < 300:
        return 2
    elif points < 600:
        return 3
    elif points < 1000:
        return 4
    elif points < 1500:
        return 5
    else:
        return 6 + (points - 1500) // 500  # Un niveau tous les 500 points après 1500