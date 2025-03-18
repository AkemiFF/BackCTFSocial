import json
import os

from dotenv import load_dotenv
from openai import APIError, AuthenticationError, OpenAI, RateLimitError

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
            - Structure en 2 parties dans les cas nécéssaires : Définition + Exemple pratique ou astuce de hacking
            - Réponds sous un format markdown détaillé et bien structuré
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
            


system_prompt_module ="""Génère un module de cours au format JSON strictement conforme à cette structure. Titre: utilise les 3 premiers mots du sujet suivi de '...'. Durée: estime-la de façon réaliste. Contenu: crée 4-6 sections dont au moins 1 lien. Les textes doivent inclure des balises HTML simples (h1, h2, h3, p, ul, li, etc) avec classes Tailwind pour la mise en forme (ex: 'text-xl font-bold mb-4'). 
Structure requise : {
    \"title\": \"string\", 
    \"duration\": \"string\", 
    \"content\": [
      {
        \"type\": \"text\",
        \"content\": \"string avec HTML/Tailwind\"
      },
      {
        \"type\": \"link\",
        \"url\": \"https://...\",
        \"description\": \"string\"
      }
    ]
  }. Ne renvoie QUE le JSON sans commentaires."""
class GenerateModule:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-3.5-turbo-0125"

    def generate_response(self, user_input):
        try:
            messages = [
                {"role": "system", "content": system_prompt_module},
                {"role": "user", "content": f"Sujet du cours : {user_input}\nGénère UNIQUEMENT le JSON valide."}
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                response_format={"type": "json_object"},  # Force le mode JSON
                stream=True
            )

            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content

            # Validation finale
            json.loads(full_response)

        except (APIError, RateLimitError, AuthenticationError) as e:
            yield json.dumps({"error": str(e)})
        except json.JSONDecodeError:
            yield json.dumps({"error": "Format de réponse invalide"})
        except Exception as e:
            yield json.dumps({"error": f"Erreur inattendue: {str(e)}"})