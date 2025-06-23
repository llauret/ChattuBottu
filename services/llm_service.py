"""
Service LLM pour ChattuBottu - Gestion des interactions avec Mistral
"""
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Optional

from config import config
from models import document_store
from services.external_resource_service import ExternalResourceService

class LLMService:
    """Service pour les interactions avec le LLM Mistral"""
    
    def __init__(self):
        self.llm = ChatMistralAI(
            model=config.MISTRAL_MODEL,
            temperature=config.MISTRAL_TEMPERATURE,
            api_key=config.MISTRAL_API_KEY
        )
        # Initialize external resource service
        self.external_service = ExternalResourceService()
    
    def get_chatbot_response(self, user_message: str) -> str:
        """Générer une réponse de chatbot contextuelle avec ressources externes"""
        context = document_store.get_recent_content(limit=3)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "Tu es un assistant pédagogique. Utilise le contexte fourni pour répondre à la question de l'utilisateur. Contexte : {context}"),
            ("user", "{question}")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            # Generate the main response
            main_response = chain.invoke({"context": context, "question": user_message})
            
            # Get external resources
            external_resources = self.external_service.get_external_resources(user_message, main_response)
            
            # Format external resources as HTML
            resources_html = self.external_service.format_external_resources_html(external_resources)
            
            # Combine main response with external resources
            full_response = main_response
            if resources_html:
                full_response += "\n\n" + resources_html
            
            return full_response
            
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
