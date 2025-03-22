from django.urls import include, path
from learn.views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'modules', ModuleViewSet)
router.register(r'user/progress', UserProgressViewSet, basename='user-progress')
router.register(r'user/certifications', CertificationViewSet, basename='user-certifications')
router.register(r'user/points/transactions', PointsTransactionViewSet, basename='points-transactions')

admin_router = DefaultRouter()
admin_router.register(r'courses', AdminCourseViewSet)
admin_router.register(r'modules', AdminModuleViewSet)
admin_router.register(r'content-items', AdminContentItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', include(admin_router.urls)), 
    path('user/points/', UserPointsView.as_view(), name='user-points'),
    path('admin/reference-data/', AdminReferenceDataView.as_view(), name='admin-reference-data'),
    path('courses/<int:course_id>/enroll/', CourseEnrollmentView.as_view(), name='enroll-course'),
    path('admin/modules/<int:module_id>/quizzes/', QuizQuestionCreateView.as_view(), name='quiz-question-create'),
    path('modules/<int:module_id>/quiz/<int:quiz_id>/', QuizQuestionUpdateView.as_view(), name='quiz-question-update'),
]