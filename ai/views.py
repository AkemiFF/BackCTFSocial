import json
import time

from ai.chatgpt import GenerateModule  # Importez votre classe GenerateModule
from ai.chatgpt import ChatGPTService
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

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
def generate_module(request):
    """
    Vue pour générer un module de cours en streaming.
    """
    try:
        # Récupérez le prompt de l'utilisateur depuis le corps de la requête
        data = json.loads(request.body)
        user_input = data.get("prompt", "")

        if not user_input:
            return JsonResponse({"error": "Le champ 'prompt' est requis"}, status=400)

        # Générez la réponse en streaming
        def stream_response():
            for chunk in module_generator.generate_response(user_input):
                yield f"data: {json.dumps({'content': chunk})}\n\n"

        return StreamingHttpResponse(stream_response(), content_type="text/event-stream")

    except json.JSONDecodeError:
        return JsonResponse({"error": "Corps de la requête invalide"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)