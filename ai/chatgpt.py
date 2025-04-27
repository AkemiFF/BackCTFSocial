import json
import logging
import os
from typing import Any, Dict

from django.conf import settings
from dotenv import load_dotenv
from openai import APIError, AuthenticationError, OpenAI, RateLimitError
from openai.types.chat import ChatCompletion

from .models import ChatHistory

logger = logging.getLogger(__name__)

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
            
system_prompt_module = """
Génère un module de cours détaillé au format JSON strictement conforme à cette structure. Respecte scrupuleusement ces consignes :

1. **Titre** :
   - Utilise les 3 premiers mots du sujet + "..."
   - Exemple : "Introduction à la..." pour "Introduction à la programmation Python"

2. **Durée** :
   - Estime réalistement (ex: "4h30" pour 3 sections théoriques + 2 exercices)
   - Format : "Xh" ou "XhXX"

3. **Contenu** (6 à 8 sections minimum) :
   - Alterner théorie (70%) et pratique (30%)
   - Chaque section doit contenir :
     * 1 sous-titre explicite avec h2/h3
     * 1 paragraphe développé (5-8 lignes)
     * Des listes à puces pour les points clés
   - Inclure obligatoirement :
     * Une introduction générale (h1)
     * Des objectifs pédagogiques (ul > li)
     * 1 cas pratique avec exemple de code
     * 2 ressources externes minimum (liens variés)

4. **Exigences de style** :
   - Utiliser des classes Tailwind
   - Balises HTML autorisées : h1, h2, h3, p, ul, ol, li, pre, code, a

Format JSON strict :
{
  "title": "string",
  "duration": "string",
  "content": [
    {
      "type": "text",
      "content": "string avec HTML/Tailwind"
    },
    {
      "type": "link",
      "url": "https://...",
      "description": "string"
    }
  ]
}

Il doit y avoir au moins 6 éléments dans content, Ne renvoie QUE le JSON validé sans commentaires. Vérifie la syntaxe avant de répondre.
"""
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
                temperature=0.5,
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
            
            
class ChatGPTEvaluator:
    SYSTEM_PROMPT = """Tu es un expert pédagogique spécialisé dans l'évaluation de réponses étudiantes. 
    Analyse la réponse selon ces critères :
    1. Pertinence par rapport à la question
    2. Précision technique
    3. Structure et clarté
    4. Exhaustivité des concepts clés
    5. Qualité des exemples
    
    Fournis une note sur 20 et un feedback constructif en JSON avec ce format :
    {
        "score": number (0-20),
        "feedback": string (3-5 points max),
        "improvement_suggestions": string[]
    }"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def evaluate_answer(self, module_title: str, question: str, answer: str) -> Dict[str, Any]:
        """
        Évalue une réponse étudiante en utilisant OpenAI GPT-4.
        
        Args:
            module_title (str): Titre du module
            question (str): Question posée
            answer (str): Réponse de l'étudiant
        
        Returns:
            Dict[str, Any]: Résultat de l'évaluation
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                temperature=0.3,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": self._build_user_prompt(module_title, question, answer)}
                ]
            )
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Erreur OpenAI: {str(e)}")
            raise ValueError("Erreur lors de l'appel à OpenAI")

    def _build_user_prompt(self, module_title: str, question: str, answer: str) -> str:
        """
        Construit le prompt utilisateur pour OpenAI.
        """
        return f"""Module: {module_title}
        Question: {question}
        Réponse étudiante: {answer}
        
        Évaluation demandée :"""

    def _parse_response(self, response: ChatCompletion) -> Dict[str, Any]:
        """
        Parse la réponse OpenAI en un format utilisable.
        """
        try:
            content = json.loads(response.choices[0].message.content)
            
            if not all(key in content for key in ['score', 'feedback', 'improvement_suggestions']):
                raise ValueError("Format de réponse OpenAI invalide")
            
            return {
                'score': max(0, min(20, int(content['score'])) if isinstance(content['score'], int) else 10),
                'feedback': content['feedback'],
                'suggestions': content['improvement_suggestions'][:3]  # Limite à 3 suggestions
            }
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Erreur de parsing OpenAI: {str(e)}")
            raise ValueError("Erreur de traitement de la réponse AI")
        

# class QuizGeneratorService2:
#     def __init__(self):
#         self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#         self.model = "gpt-3.5-turbo"

#     def _build_user_prompt(self, module, user_prompt: str, number_of_questions: int) -> str:

#         # Informations générales du module
#         module_info = (
#             f"Module: {module.title}\n"
#             f"Durée: {module.duration}\n"
#             f"Points: {module.points}\n"
#         )
#         # Récupération des contenus liés au module
#         content_info = ""
#         content_items = list(module.content_items.all())[:5]  # Limite à 5 éléments
#         for content_item in content_items:
#             if content_item.type == 'text' and hasattr(content_item, 'text_content'):
#                 content_info += f"- {content_item.get_type_display()}: {content_item.text_content.content}\n"
#             else:
#                 content_info += f"- {content_item.get_type_display()} (contenu non textuel)\n"
                
#         # Construction du prompt complet
#         prompt = f"""
#             {module_info}
#             Nombre de questions demandées: {number_of_questions}
#             Prompt utilisateur: {user_prompt}

#             Contenu du module:
#             {content_info}            
#             """
#         return prompt.strip()

#     def generate_quiz(self, user, module, prompt: str, num_questions: int, context=None):
#         system_prompt = quiz_system_prompt
        
#         messages = [
#             {"role": "system", "content": system_prompt.strip()},
#             {"role": "user", "content": self._build_user_prompt(module, prompt, num_questions)}
#         ]
        
#         try:
#             response = self.client.chat.completions.create(
#                 model="gpt-4-0125-preview",
#                 temperature=0.3,
#                 response_format={"type": "json_object"},
#                 messages=messages
#             )
#             # Extract the content from the response
#             content = response.choices[0].message.content
#             # Parse the JSON content
#             quiz_data = json.loads(content)
#             return quiz_data
#         except Exception as e:
#             error_map = {
#                 "RateLimitError": "Limite de requêtes dépassée",
#                 "AuthenticationError": "Problème d'authentification",
#                 "APIError": "Erreur de l'API"
#             }
#             return {"error": error_map.get(type(e).__name__, f"Erreur inconnue: {str(e)}")}
        
        
class QuizGeneratorService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4-0125-preview"
        
    def generate_quiz(self,data):
        try:
            quiz_system_prompt = f"""
                Tu es un générateur expert de quiz éducatifs. Respecte STRICTEMENT ces règles :

                1. Génère EXACTEMENT {data['num_questions']} questions, 30% ouvertes et 70% QCM sauf si le contraire est demandé
                2. Format JSON VALIDE avec une liste d'objets
                3. Chaque question doit avoir :
                - Un 'id' unique (débutant à 1)
                - Un 'type' valide (multiple-choice/open-ended)
                - Un 'order' correspondant à sa difficulté (1-{data['num_questions']})
                - Des 'options' cohérentes pour les QCM

                Exemple VALIDE :
                {{"quiz":[
                    {{
                        "id": 1,
                        "question": "Question ouverte exemple?",
                        "type": "open-ended",
                        "order": 1,
                        "options": []
                    }},
                    {{
                        "id": 2,
                        "question": "QCM exemple?",
                        "type": "multiple-choice",
                        "order": 2,
                        "options": [
                            {{"id": 1, "text": "Bonne réponse", "is_correct": true}},
                            {{"id": 2, "text": "Mauvaise réponse", "is_correct": false}}
                        ]
                    }}
                ]}}
                """
            supplement = ""
            if (data["question_type"] == "both"):
                supplement  = f'\nTout les questions doivent être de type {data["question_type"]}'
            messages = [
                {"role": "assistant", "content": quiz_system_prompt},
                {"role": "user", "content": f"Sujet du module : {data['module'].title}\nPrompt de l'utilisateur : {data['prompt']}\n Nombre de quiz a générer : {data["num_questions"]}{supplement}\n\nGénère UNIQUEMENT le JSON valide."}
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2000,
                temperature=0.8,
                response_format={"type": "json_object"},  # Force le mode JSON
            )
            

            content = response.choices[0].message.content
            print(content)
            quiz_data = json.loads(content)
            # logger.info(f"Quiz généré: {quiz_data}")
            # Validation de la structure
            if not isinstance(quiz_data["quiz"], list) :
                raise ValueError("Structure de données invalide")
                
            return quiz_data["quiz"]

        except Exception as e:
            error_map = {
                "RateLimitError": "Limite de requêtes dépassée",
                "AuthenticationError": "Problème d'authentification",
                "APIError": "Erreur de l'API"
            }
            print( error_map.get(type(e).__name__, str(e)))
            return {"error": error_map.get(type(e).__name__, str(e))}