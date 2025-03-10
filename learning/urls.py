# learning/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CourseViewSet, LearningPathViewSet, ModuleViewSet,
                    QuestionViewSet, QuizViewSet, UserCourseProgressViewSet,
                    UserModuleProgressViewSet, UserQuizAttemptViewSet)

router = DefaultRouter()
router.register(r'learning-paths', LearningPathViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'modules', ModuleViewSet)
router.register(r'quizzes', QuizViewSet)
router.register(r'questions', QuestionViewSet)
router.register(r'course-progress', UserCourseProgressViewSet, basename='course-progress')
router.register(r'module-progress', UserModuleProgressViewSet, basename='module-progress')
router.register(r'quiz-attempts', UserQuizAttemptViewSet, basename='quiz-attempts')

urlpatterns = [
    path('', include(router.urls)),
]