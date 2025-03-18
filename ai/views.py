import json
import logging
import time

from ai.chatgpt import GenerateModule  # Importez votre classe GenerateModule
from ai.chatgpt import ChatGPTService
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from learn.models import Course
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .chatgpt import ChatGPTEvaluator

logger = logging.getLogger(__name__)

module_generator = GenerateModule()


@api_view(['POST'])
@permission_classes([AllowAny])
def chat_stream(request):
    prompt = request.data.get('prompt')
    context = request.data.get('context', {})
    last_request = request.session.get('last_ai_request')
    if last_request and time.time() - last_request < 2:  # 2 secondes entre les requêtes
        return Response({"error": "Attendez avant de faire une nouvelle demande"}, status=429)
    
    request.session['last_ai_request'] = time.time()
    def event_stream():
        service = ChatGPTService()
        try:
            for chunk in service.generate_response(request.user, prompt, context):               
                if isinstance(chunk, dict) and 'error' in chunk:
                    yield f"data: {json.dumps(chunk)}\n\n"
                else:
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            print("Error in stream:", e)  # <-- Ajoutez ce log
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

prompt = """{
    "id": 8,
    "title": "Introduction à Python",
    "slug": "introduction-a-python",
    "description": "Un cours de base pour apprendre la programmation avec Python.",
    "level": "debutant",
    "category": "web",
    "duration": "5 heures",
    "prerequisites": "Linux Pour les cons",
    "instructor": "Dr Akemi",
    "image": "http://localhost:8000/media/courses/66fe8160d3013f6e008a0279_www.forgge.work_4041440_eQe3XPF.webp",
    "students": 0,
    "rating": "0.0",
    "modules": [
        {
            "id": 13,
            "title": "Les bases de Python",
            "duration": "1h",
            "order": 0,
            "points": 10,
            "completed": false
        },
        {
            "id": 14,
            "title": "Suite Intro Python",
            "duration": "5h",
            "order": 0,
            "points": 10,
            "completed": false
        },
        {
            "id": 15,
            "title": "Module généré: un truc...",
            "duration": "2h 30min",
            "order": 0,
            "points": 10,
            "completed": false
        }
    ],
    "progress": 0,
    "certification": null
}"""
@csrf_exempt
@require_http_methods(["POST"])
def generate_module2(request):
    """
    Vue pour générer un module de cours et retourner les données finales.
    """
    try:
        # Récupérez le prompt de l'utilisateur depuis le corps de la requête
        data = json.loads(request.body)
        print(data)
        user_input = data.get("prompt", "")

        if not user_input:
            return JsonResponse({"error": "Le champ 'prompt' est requis"}, status=400)

        # Accumuler tous les chunks dans une variable
        full_response = ""
        for chunk in module_generator.generate_response(user_input):
            full_response += chunk  
        print(full_response)
        
        return JsonResponse({"content": full_response}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Corps de la requête invalide"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
    
@csrf_exempt
@require_http_methods(["POST"])
def generate_module(request):
    """
    Vue pour générer un module de cours en fonction du contexte du cours existant
    """
    try:
        data = json.loads(request.body)
        course_id = data.get("course_id")
        user_prompt = data.get("prompt", "")
        
        if not course_id or not user_prompt:
            return JsonResponse({"error": "Les champs 'course_id' et 'prompt' sont requis"}, status=400)

        # Récupération du cours et de ses modules existants
        try:
            course = Course.objects.prefetch_related('modules').get(id=course_id)
        except Course.DoesNotExist:
            return JsonResponse({"error": "Cours introuvable"}, status=404)

        # Construction du contexte détaillé
        course_context = f"""
        [Contexte du Cours]
        Titre du cours: {course.title}
        Niveau: {course.get_level_display()}
        Catégorie: {course.category}
        Description: {course.description}
        Modules existants:
        {chr(10).join([f"- {module.title} ({module.duration}) | Points: {module.points}" for module in course.modules.all()])}
        """

        # Création du prompt enrichi
        enhanced_prompt = f"""
        {course_context}

        [Consignes de Génération]
        {user_prompt}
        - Adapter le contenu au niveau {course.get_level_display().lower()} 
        - Éviter les doublons avec les modules existants
        - Respecter la structure pédagogique du cours
        - Intégrer des références à la description: "{course.description[:200]}..."
        """

        # Génération du module avec le contexte
        full_response = ""
        for chunk in module_generator.generate_response(enhanced_prompt):
            full_response += chunk

        # Validation et retour du résultat
        try:
            parsed_response = json.loads(full_response)
            return JsonResponse(parsed_response, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Réponse AI invalide"}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Corps de requête JSON invalide"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Erreur serveur: {str(e)}"}, status=500)
    
@method_decorator(csrf_exempt, name='dispatch')
class EvaluateAnswerView(View):
    def post(self, request):
        """
        Endpoint pour évaluer une réponse étudiante.
        """
        try:
            data = json.loads(request.body)
            required_fields = ['moduleTitle', 'question', 'answer']
            
            if not all(field in data for field in required_fields):
                return JsonResponse(
                    {'error': 'Champs manquants: moduleTitle, question ou answer'}, 
                    status=400
                )

            evaluator = ChatGPTEvaluator()
            evaluation = evaluator.evaluate_answer(
                data['moduleTitle'],
                data['question'],
                data['answer']
            )
            return JsonResponse(evaluation)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Format JSON invalide'}, status=400)
        except ValueError as e:
            logger.error(f"Erreur de validation: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Erreur serveur: {str(e)}")
            return JsonResponse(
                {'error': f"Erreur lors de l'évaluation: {str(e)}"}, 
                status=500
            )