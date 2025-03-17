import os

from dotenv import load_dotenv
from openai import OpenAI

from .models import ChatHistory

load_dotenv()

class ChatGPTService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-3.5-turbo"
        self.max_history = int(os.getenv("HISTORY_LENGTH", 5))

    def get_chat_history(self, user):
        if not user or not user.id:
            return []
        return ChatHistory.objects.filter(user=user).order_by('-timestamp')[:self.max_history]

    def generate_response(self, user, prompt, context=None):
        try:
            # Récupération de l'historique
            history = self.get_chat_history(user)
            system_prompt = """
            Tu es un professeur expert en développement, programmation et hacking. Explique le concept suivant de manière claire et concise :
            - Utilise des analogies concrètes et des exemples de code
            - Limite ta réponse à 3 phrases maximum
            - Adopte un ton encourageant et motivant
            - Structure en 2 parties : Définition + Exemple pratique ou astuce de hacking
            """
            messages = [{
                "role": "system",
                "content": system_prompt
            }]

            # Construction du contexte historique
            for h in reversed(history):
                messages.extend([
                    {"role": "user", "content": h.prompt},
                    {"role": "assistant", "content": h.response}
                ])

            messages.append({"role": "user", "content": prompt})

            # Appel à l'API OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                stream=True
            )

            full_response = ""
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:  
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
                    
            ChatHistory.objects.create(
                user=user,
                prompt=prompt,
                response=full_response,
                context=context or {}
            )

        except Exception as e:
            print(f"Error in generate_response: {str(e)}")
            error_map = {
                "RateLimitError": "Limite de requêtes dépassée",
                "AuthenticationError": "Problème d'authentification",
                "APIError": "Erreur de l'API"
            }
            yield {"error": error_map.get(type(e).__name__, f"Erreur inconnue: {str(e)}")}