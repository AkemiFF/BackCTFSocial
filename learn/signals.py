from django.contrib.auth.models import User
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import (Certification, ModuleCompletion, PointsTransaction,
                     QuizAttempt, UserProfile)
from .utils import update_course_progress


@receiver(post_save, sender=ModuleCompletion)
def award_points_for_module_completion(sender, instance, created, **kwargs):
    if created:
        points = instance.module.points
        user_profile = instance.user.profile
        user_profile.points += points
        user_profile.save()
        
        # Enregistrer la transaction de points
        PointsTransaction.objects.create(
            user=instance.user,
            points=points,
            transaction_type='module_completion',
            description=f"Complétion du module: {instance.module.title}"
        )
        
        # Mettre à jour la progression du cours
        update_course_progress(instance.user, instance.module.course)

@receiver(post_save, sender=QuizAttempt)
def award_points_for_quiz_success(sender, instance, created, **kwargs):
    if created and instance.score / instance.total_questions >= 0.7:  # 70% de réussite
        points = instance.module.points // 2  # La moitié des points du module pour le quiz
        user_profile = instance.user.profile
        user_profile.points += points
        user_profile.save()
        
        # Enregistrer la transaction de points
        PointsTransaction.objects.create(
            user=instance.user,
            points=points,
            transaction_type='quiz_success',
            description=f"Réussite du quiz: {instance.module.title}"
        )

@receiver(post_save, sender=Certification)
def award_points_for_certification(sender, instance, created, **kwargs):
    if created:
        # Bonus de points pour l'obtention d'une certification
        points = 100  # Valeur arbitraire, à ajuster selon vos besoins
        user_profile = instance.user.profile
        user_profile.points += points
        user_profile.save()
        
        # Enregistrer la transaction de points
        PointsTransaction.objects.create(
            user=instance.user,
            points=points,
            transaction_type='certification',
            description=f"Certification obtenue: {instance.course.title}"
        )