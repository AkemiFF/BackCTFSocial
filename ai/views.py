import json
import time

from ai.chatgpt import ChatGPTService
from django.http import StreamingHttpResponse
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


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
