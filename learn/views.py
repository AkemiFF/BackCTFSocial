import json

from accounts.models import *
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from learn.models import (Certification, ContentItem, Course, Module,
                          ModuleCompletion, PointsTransaction, QuizAnswer,
                          QuizAttempt, QuizOption, QuizQuestion, Tag,
                          UserProgress)
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .admin_serializers import (AdminQuizQuestionSerializer,
                                ContentItemCreateSerializer,
                                CourseCreateSerializer, ModuleCreateSerializer)
from .serializers import (CertificationSerializer, CourseDetailSerializer,
                          CourseListSerializer, ModuleDetailSerializer,
                          ModuleListSerializer, PointsTransactionSerializer,
                          QuizQuestionSerializer, QuizSubmissionSerializer,
                          TagSerializer, UserPointsSerializer,
                          UserProgressSerializer)
from .utils import calculate_user_level, update_course_progress


class QuizQuestionUpdateView(APIView):
    def put(self, request, module_id, quiz_id):
        # Vérifier que le module existe
        try:
            module = Module.objects.get(id=module_id)
        except Module.DoesNotExist:
            return Response({"error": "Module non trouvé"}, status=status.HTTP_404_NOT_FOUND)

        # Vérifier que la question du quiz existe
        try:
            question = QuizQuestion.objects.get(id=quiz_id, module=module)
        except QuizQuestion.DoesNotExist:
            return Response({"error": "Quiz non trouvé pour ce module"}, status=status.HTTP_404_NOT_FOUND)

        # Mettre à jour la question du quiz
        serializer = AdminQuizQuestionSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class AdminReferenceDataView(APIView):
    """
    API endpoint pour récupérer les données de référence pour les formulaires d'administration
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Récupérer les cours pour le formulaire d'ajout de module
        courses = Course.objects.all()
        courses_data = CourseListSerializer(courses, many=True, context={'request': request}).data
        
        # Récupérer les tags existants pour le formulaire d'ajout de cours
        tags = Tag.objects.all()
        tags_data = TagSerializer(tags, many=True).data
        
        # Récupérer les niveaux et catégories pour le formulaire d'ajout de cours
        levels = [
            {'value': 'debutant', 'label': 'Débutant'},
            {'value': 'intermediaire', 'label': 'Intermédiaire'},
            {'value': 'avance', 'label': 'Avancé'},
        ]
        
        categories = [
            {'value': 'reseaux', 'label': 'Réseaux'},
            {'value': 'web', 'label': 'Web'},
            {'value': 'exploitation', 'label': 'Exploitation'},
            {'value': 'forensic', 'label': 'Forensic'},
            {'value': 'cryptographie', 'label': 'Cryptographie'},
        ]
        
        return Response({
            'courses': courses_data,
            'tags': tags_data,
            'levels': levels,
            'categories': categories,
        })

class AdminCourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour la gestion des cours (admin)
    """
    queryset = Course.objects.all()
    serializer_class = CourseCreateSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def create(self, request, *args, **kwargs):
        """
        Créer un nouveau cours
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
   
        title = serializer.validated_data.get('title')
        slug = slugify(title)
        unique_slug = slug
        num = 1      
        
        while Course.objects.filter(slug=unique_slug).exists():
            unique_slug = f'{slug}-{num}'
            num += 1
        serializer.validated_data['slug'] = unique_slug
        try:
            with transaction.atomic():
                course = serializer.save()
                return Response(
                    {'id': course.id, 'message': 'Cours créé avec succès'},
                    status=status.HTTP_201_CREATED
                )
        except Exception as e:
            print(serializer.errors)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class AdminModuleViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour la gestion des modules (admin)
    """
    queryset = Module.objects.all()
    serializer_class = ModuleCreateSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def create(self, request, *args, **kwargs):
        """
        Créer un nouveau module
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                module = serializer.save()
                return Response(
                    {'id': module.id, 'message': 'Module créé avec succès'},
                    status=status.HTTP_201_CREATED
                )
        except Exception as e:
            # print(e)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def add_content(self, request, pk=None):
        """
        Ajouter un élément de contenu à un module
        """
        module = self.get_object()
        
        # Ajouter le module à la requête
        data = request.data.copy()
        data['module'] = module.id
        
        serializer = ContentItemCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                content_item = serializer.save()
                return Response(
                    {'id': content_item.id, 'message': 'Contenu ajouté avec succès'},
                    status=status.HTTP_201_CREATED
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['put'])
    def reorder_content(self, request, pk=None):
        """
        Réordonner les éléments de contenu d'un module
        """
        module = self.get_object()
        
        # Format attendu: [{'id': 1, 'order': 0}, {'id': 2, 'order': 1}, ...]
        items_order = request.data.get('items', [])
        
        if not items_order:
            return Response(
                {'error': 'Aucun élément à réordonner'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                for item_data in items_order:
                    item_id = item_data.get('id')
                    new_order = item_data.get('order')
                    
                    if item_id is None or new_order is None:
                        continue
                    
                    content_item = get_object_or_404(ContentItem, id=item_id, module=module)
                    content_item.order = new_order
                    content_item.save()
                
                return Response({'message': 'Contenu réordonné avec succès'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class AdminContentItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour la gestion des éléments de contenu (admin)
    """
    queryset = ContentItem.objects.all()
    serializer_class = ContentItemCreateSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour les cours
    """
    queryset = Course.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'instructor']
    ordering_fields = ['title', 'created_at', 'students', 'rating']
    
    def get_serializer_class(self):
        if self.action == 'retrieve' :
            return CourseDetailSerializer
        return CourseListSerializer
    
    def get_queryset(self):
        queryset = Course.objects.prefetch_related(
            'modules', 
            'course_tags__tag',            
        ).all()
        
        # Filtrer par niveau
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)
        
        # Filtrer par catégorie
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filtrer par tag
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(course_tags__tag__name=tag)
        
        # Trier les cours
        sort = self.request.query_params.get('sort')
        if sort == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort == 'popular':
            queryset = queryset.order_by('-students')
        elif sort == 'rating':
            queryset = queryset.order_by('-rating')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        Récupérer toutes les catégories de cours
        """
        categories = Course.objects.values_list('category', flat=True).distinct()
        return Response(categories)
    
    @action(detail=False, methods=['get'])
    def tags(self, request):
        """
        Récupérer tous les tags de cours
        """
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def modules(self, request, pk=None):
        """
        Récupérer tous les modules d'un cours
        """
        course = self.get_object()
        modules = Module.objects.filter(course=course).order_by('order')
        serializer = ModuleListSerializer(modules, many=True, context={'request': request})
        return Response(serializer.data)

class ModuleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour les modules
    """
    queryset = Module.objects.all()
    serializer_class = ModuleDetailSerializer
    
    @action(detail=True, methods=['get'])
    def content(self, request, pk=None):
        """
        Récupérer le contenu d'un module
        """
        module = self.get_object()
        content_items = ContentItem.objects.filter(module=module).order_by('order')
        serializer = self.get_serializer(module)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def quiz(self, request, pk=None):
        """
        Récupérer les questions du quiz d'un module
        """
        module = self.get_object()
        questions = QuizQuestion.objects.filter(module=module).order_by('order')
        serializer = QuizQuestionSerializer(questions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def submit_quiz(self, request, pk=None):
        """
        Soumettre les réponses d'un quiz
        """
        module = self.get_object()
        serializer = QuizSubmissionSerializer(data=request.data)
        
        if serializer.is_valid():
            answers_data = serializer.validated_data['answers']
            time_spent = serializer.validated_data['time_spent']
            
            # Créer une tentative de quiz
            quiz_attempt = QuizAttempt.objects.create(
                user=request.user,
                module=module,
                time_spent=time_spent
            )
            
            # Traiter les réponses
            score = 0
            total_questions = 0
            feedback = []
            
            for answer_data in answers_data:
                question_id = answer_data['question_id']
                answer = answer_data['answer']
                
                try:
                    question = QuizQuestion.objects.get(id=question_id, module=module)
                    
                    if question.type == 'multiple-choice':
                        total_questions += 1
                        selected_option_id = answer
                        selected_option = QuizOption.objects.get(id=selected_option_id)
                        is_correct = selected_option.is_correct
                        
                        if is_correct:
                            score += 1
                        
                        # Enregistrer la réponse
                        quiz_answer = QuizAnswer.objects.create(
                            attempt=quiz_attempt,
                            question=question,
                            selected_option=selected_option,
                            is_correct=is_correct
                        )
                        
                        # Préparer le feedback
                        correct_option = QuizOption.objects.filter(question=question, is_correct=True).first()
                        feedback.append({
                            'question_id': question.id,
                            'correct': is_correct,
                            'feedback': 'Bonne réponse !' if is_correct else f'La réponse correcte était : {correct_option.text}'
                        })
                    
                    elif question.type == 'open-ended':
                        # Pour les questions ouvertes, on enregistre simplement la réponse
                        open_answer = answer
                        
                        QuizAnswer.objects.create(
                            attempt=quiz_attempt,
                            question=question,
                            open_answer=open_answer
                        )
                
                except (QuizQuestion.DoesNotExist, QuizOption.DoesNotExist) as e:
                    return Response(
                        {'error': f'Question ou option invalide: {str(e)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Mettre à jour le score de la tentative
            quiz_attempt.score = score
            quiz_attempt.total_questions = total_questions
            quiz_attempt.save()
            
            # Vérifier si le quiz est réussi (70% de bonnes réponses)
            is_passed = total_questions > 0 and (score / total_questions) >= 0.7
            
            # Si le quiz est réussi, marquer le module comme complété
            if is_passed and not ModuleCompletion.objects.filter(user=request.user, module=module).exists():
                ModuleCompletion.objects.create(
                    user=request.user,
                    module=module,
                    time_spent=time_spent
                )
                
                # Mettre à jour la progression du cours
                update_course_progress(request.user, module.course)
            
            result = {
                'score': score,
                'total': total_questions,
                'passed': is_passed,
                'feedback': feedback
            }
            
            return Response(result)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Marquer un module comme complété
        """
        module = self.get_object()
        
        # Vérifier si le module est déjà complété
        if ModuleCompletion.objects.filter(user=request.user, module=module).exists():
            return Response({'message': 'Module déjà complété'})
        
        # Marquer le module comme complété
        time_spent = request.data.get('time_spent', 0)
        ModuleCompletion.objects.create(
            user=request.user,
            module=module,
            time_spent=time_spent
        )
        
        # Mettre à jour la progression du cours
        update_course_progress(request.user, module.course)
        
        return Response({'message': 'Module marqué comme complété'})

class UserProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour la progression de l'utilisateur
    """
    serializer_class = UserProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserProgress.objects.filter(user=self.request.user).select_related('course')
    
    @action(detail=False, methods=['get'])
    def course(self, request):
        """
        Récupérer la progression de l'utilisateur pour un cours spécifique
        """
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response(
                {'error': 'Paramètre course_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        course = get_object_or_404(Course, id=course_id)
        
        # Récupérer ou créer la progression
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={'progress': 0}
        )
        
        serializer = self.get_serializer(progress)
        return Response(serializer.data)

class CertificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour les certifications de l'utilisateur
    """
    serializer_class = CertificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Certification.objects.filter(user=self.request.user).select_related('course')

class UserPointsView(generics.RetrieveAPIView):
    """
    API endpoint pour les points et le niveau de l'utilisateur
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserPointsSerializer
    
    def get_object(self):
        user_profile, created = User.objects.get_or_create(
            user=self.request.user,
            defaults={'points': 0}
        )
        
        user_points = user_profile.points
        user_level = calculate_user_level(user_points)
        
        # Calculer les points nécessaires pour le prochain niveau
        next_level_points = 0
        if user_level == 1:
            next_level_points = 100
        elif user_level == 2:
            next_level_points = 300
        elif user_level == 3:
            next_level_points = 600
        elif user_level == 4:
            next_level_points = 1000
        elif user_level == 5:
            next_level_points = 1500
        else:
            next_level_points = 1500 + (user_level - 5) * 500
        
        # Calculer la progression vers le prochain niveau
        if user_level == 1:
            level_progress = (user_points / 100) * 100
        elif user_level == 2:
            level_progress = ((user_points - 100) / 200) * 100
        elif user_level == 3:
            level_progress = ((user_points - 300) / 300) * 100
        elif user_level == 4:
            level_progress = ((user_points - 600) / 400) * 100
        elif user_level == 5:
            level_progress = ((user_points - 1000) / 500) * 100
        else:
            level_progress = ((user_points - next_level_points + 500) / 500) * 100
        
        return {
            'points': user_points,
            'level': user_level,
            'next_level_points': next_level_points,
            'level_progress': level_progress
        }

class PointsTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour l'historique des transactions de points
    """
    serializer_class = PointsTransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PointsTransaction.objects.filter(user=self.request.user).order_by('-created_at')


class CourseEnrollmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        
        # Créer UserProgress
        UserProgress.objects.get_or_create(user=request.user, course=course)
        
        # Incrémenter le compteur students
        Course.objects.filter(id=course_id).update(students=models.F('students') + 1)
        
        return Response({"message": "Inscription réussie"}, status=201)
    
    

class QuizQuestionCreateView(APIView):
    def post(self, request, module_id):
        # Vérifier que le module existe
        try:
            module = Module.objects.get(id=module_id)
        except Module.DoesNotExist:
            return Response({"error": "Module non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        
        # Intégrer l'ID du module dans les données envoyées si ce n'est pas déjà fait
        data = request.data.copy()
        data['module'] = module.id

        serializer = AdminQuizQuestionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
