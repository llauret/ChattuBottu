"""
Service LLM pour ChattuBottu - Gestion des interactions avec Mistral
"""
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Optional

from config import config
from models import document_store

class LLMService:
    """Service pour les interactions avec le LLM Mistral"""
    
    def __init__(self):
        self.llm = ChatMistralAI(
            model=config.MISTRAL_MODEL,
            temperature=config.MISTRAL_TEMPERATURE,
            api_key=config.MISTRAL_API_KEY
        )
    
    def get_chatbot_response(self, user_message: str) -> str:
        """Générer une réponse de chatbot contextuelle avec explications techniques détaillées"""
        context = document_store.get_recent_content(limit=3)
        
        # Détecter si c'est une question technique nécessitant des exemples de code
        is_technical = self._is_technical_question(user_message)
        
        if is_technical:
            return self._get_technical_response(user_message, context)
        else:
            return self._get_standard_response(user_message, context)
    
    def _is_technical_question(self, message: str) -> bool:
        """Détecter si la question nécessite des explications techniques avec code"""
        technical_keywords = [
            'algorithme', 'code', 'python', 'javascript', 'programmation', 'fonction',
            'variable', 'boucle', 'condition', 'classe', 'méthode', 'syntaxe',
            'exemple', 'démonstration', 'étape', 'comment faire', 'implémenter',
            'calculer', 'résoudre', 'formule', 'équation', 'mathématiques',
            'structure de données', 'tri', 'recherche', 'récursion'        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in technical_keywords)
    
    def _get_technical_response(self, user_message: str, context: str) -> str:
        """Générer une réponse technique détaillée avec exemples de code"""
        
        # Importer ici pour éviter les imports circulaires
        try:
            from services.technical_explanation_service import technical_explanation_service
            
            # Utiliser le service spécialisé pour les explications techniques
            explanation_result = technical_explanation_service.generate_step_by_step_explanation(
                user_message, context
            )
            
            if explanation_result["success"]:
                return explanation_result["explanation"]
            else:
                # Fallback vers le prompt standard amélioré
                return self._get_enhanced_technical_fallback(user_message, context)
                
        except ImportError:
            # Fallback si le service n'est pas disponible
            return self._get_enhanced_technical_fallback(user_message, context)
    
    def _get_enhanced_technical_fallback(self, user_message: str, context: str) -> str:
        """Fallback amélioré pour les réponses techniques"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             """Tu es un assistant pédagogique expert en programmation et mathématiques. 
             Quand tu expliques des concepts techniques, suis cette structure :

             1. **Explication conceptuelle** : Explique le concept de manière claire
             2. **Étapes détaillées** : Décompose le processus étape par étape
             3. **Exemple concret** : Fournis un exemple pratique avec code
             4. **Code exécutable** : Inclus du code Python simple et commenté
             5. **Variantes/Extensions** : Montre des variantes ou cas d'usage

             IMPORTANT : Pour le code Python, utilise ce format spécial :
             ```python-executable
             # Ton code Python ici
             # Il sera exécutable dans le navigateur
             ```

             Utilise le contexte fourni si pertinent. Contexte : {context}"""),
            ("user", "{question}")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            return chain.invoke({"context": context, "question": user_message})
        except Exception as e:
            return f"Erreur lors de l'appel au LLM : {e}"
    
    def _get_standard_response(self, user_message: str, context: str) -> str:
        """Générer une réponse standard"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "Tu es un assistant pédagogique bienveillant. Utilise le contexte fourni pour répondre à la question de l'utilisateur de manière claire et structurée. Contexte : {context}"),
            ("user", "{question}")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            return chain.invoke({"context": context, "question": user_message})
        except Exception as e:
            return f"Erreur lors de l'appel au LLM : {e}"
    
    def generate_mindmap_markdown(self, user_message: str) -> str:
        """Générer une mindmap en markdown"""
        context = document_store.get_recent_content(limit=3)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "Tu es un assistant pédagogique. Génère une mindmap synthétique et hiérarchique en markdown (format markmap) pour la question ou le sujet donné. "
             "Utilise le contexte fourni si disponible. La mindmap doit commencer par un titre racine, puis des sous-nœuds, etc. "
             "N'ajoute aucun texte hors du markdown. Contexte : {context}"),
            ("user", "{question}")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            return chain.invoke({"context": context, "question": user_message})
        except Exception as e:
            return f"Erreur lors de la génération de la mindmap : {e}"
    
    def generate_revision_sheet(self) -> str:
        """Générer une fiche de révision basée sur les documents ingérés"""
        if not document_store.has_documents():
            return "Aucun document ingéré. Veuillez d'abord télécharger des PDF ou documents."
        
        context = "\n\n".join(document_store.get_ingested_content())
        
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "Tu es un assistant pédagogique expert. À partir des documents fournis, génère une fiche de révision complète et structurée en markdown. "
             "La fiche doit contenir : "
             "1. Un titre principal, "
             "2. Les concepts clés avec définitions, "
             "3. Les points importants à retenir, "
             "4. Des exemples concrets si disponibles, "
             "5. Des questions de révision. "
             "Utilise un format markdown avec des titres, listes à puces, et mise en forme appropriée. "
             "Contexte des documents : {context}"),
            ("user", "Génère une fiche de révision synthétique et complète basée sur les documents ingérés.")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            return chain.invoke({"context": context})
        except Exception as e:
            return f"Erreur lors de la génération de la fiche de révision : {e}"
    
    def get_completion(self, prompt: str) -> str:
        """Obtenir une completion simple du LLM"""
        try:
            simple_prompt = ChatPromptTemplate.from_messages([
                ("user", "{prompt}")
            ])
            chain = simple_prompt | self.llm | StrOutputParser()
            return chain.invoke({"prompt": prompt})
        except Exception as e:
            raise Exception(f"Erreur lors de l'appel au LLM : {e}")

# Instance globale du service LLM
llm_service = LLMService()
