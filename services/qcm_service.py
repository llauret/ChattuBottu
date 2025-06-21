"""
Service de gestion des QCM
"""
import json
import uuid
import re
from datetime import datetime
from typing import List, Dict, Any

from models import QCM, QCMQuestion, QCMResult, qcm_store, document_store, progress_store
from services.llm_service import llm_service


def clean_and_parse_json(response: str) -> dict:
    """Nettoie et parse la réponse JSON du LLM"""
    try:
        # Supprimer les balises markdown si présentes
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*$', '', response)
        
        # Supprimer les espaces en début et fin
        response = response.strip()
        
        # Chercher le premier { et le dernier }
        start = response.find('{')
        end = response.rfind('}')
        
        if start != -1 and end != -1:
            json_str = response[start:end+1]
            return json.loads(json_str)
        else:
            raise ValueError("Aucun JSON valide trouvé dans la réponse")
            
    except json.JSONDecodeError as e:
        raise ValueError(f"Erreur de parsing JSON: {str(e)}")
    except Exception as e:
        raise ValueError(f"Erreur lors du nettoyage: {str(e)}")


class QCMService:
    """Service pour gérer les QCM"""
    
    def create_fallback_qcm(self, num_questions: int) -> dict:
        """Créer un QCM de fallback si le LLM échoue"""
        questions_pool = [
            {
                "question": "Quel est l'objectif principal de l'ingestion de documents dans ce système ?",
                "options": [
                    "Stocker des fichiers pour les télécharger plus tard",
                    "Fournir du contexte à l'IA pour des réponses personnalisées",
                    "Créer des sauvegardes automatiques",
                    "Compresser les documents PDF"
                ],
                "correct_answer": 1,
                "explanation": "L'ingestion de documents permet à l'IA d'avoir du contexte pour répondre de façon personnalisée aux questions."
            },
            {
                "question": "Quels formats de fichiers sont supportés par le système ?",
                "options": [
                    "Seulement PDF",
                    "PDF, TXT, MD, CSV",
                    "Tous les formats d'images",
                    "Seulement les fichiers texte"
                ],
                "correct_answer": 1,
                "explanation": "Le système supporte les formats PDF, TXT, MD (Markdown) et CSV pour l'ingestion."
            },
            {
                "question": "Comment le système traite-t-il les documents trop longs ?",
                "options": [
                    "Il les rejette automatiquement",
                    "Il les divise en plusieurs parties",
                    "Il crée un résumé bag-of-words",
                    "Il les compresse"
                ],
                "correct_answer": 2,
                "explanation": "Le système crée un résumé bag-of-words pour les documents dépassant 8000 caractères afin de respecter les limites de tokens."
            },
            {
                "question": "Quel est l'avantage principal d'un système de chat avec documents intégrés ?",
                "options": [
                    "Réduction de l'espace de stockage",
                    "Réponses contextuelles basées sur vos documents",
                    "Chiffrement automatique des données",
                    "Traduction automatique"
                ],
                "correct_answer": 1,
                "explanation": "Le principal avantage est d'obtenir des réponses personnalisées et contextuelles basées sur vos propres documents."
            },
            {
                "question": "Que permet la fonctionnalité mindmap dans le système ?",
                "options": [
                    "Créer des graphiques statistiques",
                    "Visualiser les relations entre concepts",
                    "Compresser les fichiers",
                    "Sauvegarder automatiquement"
                ],
                "correct_answer": 1,
                "explanation": "La mindmap permet de visualiser les relations et connexions entre les différents concepts abordés dans vos documents."
            }
        ]
        
        # Sélectionner le nombre de questions demandé
        selected_questions = questions_pool[:min(num_questions, len(questions_pool))]
        
        return {
            "title": "QCM de démonstration du système",
            "questions": selected_questions
        }
    
    def generate_qcm(self, num_questions: int = 5) -> Dict[str, Any]:
        """Générer un QCM basé sur les documents ingérés"""
        if not document_store.has_documents():
            return {
                "success": False,
                "error": "Aucun document ingéré. Veuillez d'abord télécharger des PDF ou documents."
            }
        
        try:
            # Récupérer le contexte des documents
            context = document_store.get_recent_content()
            documents = document_store.get_documents()
            doc_names = [doc.filename for doc in documents]
            
            # Prompt amélioré pour générer le QCM
            prompt = f"""Tu es un assistant pédagogique expert. À partir des documents fournis, génère un QCM de {num_questions} questions.

IMPORTANT: Tu dois retourner UNIQUEMENT un JSON valide, sans aucun texte avant ou après. Pas de markdown, pas d'explication, juste le JSON brut.

Structure JSON requise :
{{
    "title": "QCM sur [sujet principal des documents]",
    "questions": [
        {{
            "question": "Quelle est... ?",
            "options": ["Réponse A", "Réponse B", "Réponse C", "Réponse D"],
            "correct_answer": 0,
            "explanation": "La réponse A est correcte car..."
        }}
    ]
}}

Règles strictes :
- Exactement {num_questions} questions
- 4 options par question (A, B, C, D)
- correct_answer: nombre 0-3 (0=A, 1=B, 2=C, 3=D)
- Questions basées sur le contenu des documents
- Options plausibles mais une seule correcte
- Explications claires

Contexte des documents : {context}

JSON:"""
            
            response = llm_service.get_completion(prompt)
            
            # Debug: afficher la réponse brute pour diagnostiquer
            print("=== RÉPONSE LLM BRUTE ===")
            print(response)
            print("=== FIN RÉPONSE ===")
            
            # Parser la réponse JSON avec nettoyage
            try:
                qcm_data = clean_and_parse_json(response)
            except ValueError as e:
                raise Exception(f"Format JSON invalide: {str(e)}. Réponse reçue: {response[:200]}...")
            
            # Validation des données QCM
            if not isinstance(qcm_data, dict):
                raise Exception("La réponse n'est pas un objet JSON valide")
            
            if "title" not in qcm_data or "questions" not in qcm_data:
                raise Exception("Champs 'title' ou 'questions' manquants dans la réponse")
            
            if not isinstance(qcm_data["questions"], list):
                raise Exception("Le champ 'questions' doit être une liste")
            
            if len(qcm_data["questions"]) != num_questions:
                raise Exception(f"Nombre de questions incorrect: {len(qcm_data['questions'])} au lieu de {num_questions}")
            
            # Validation de chaque question
            for i, q_data in enumerate(qcm_data["questions"]):
                if not isinstance(q_data, dict):
                    raise Exception(f"Question {i+1} n'est pas un objet valide")
                
                required_fields = ["question", "options", "correct_answer", "explanation"]
                for field in required_fields:
                    if field not in q_data:
                        raise Exception(f"Champ '{field}' manquant dans la question {i+1}")
                
                if not isinstance(q_data["options"], list) or len(q_data["options"]) != 4:
                    raise Exception(f"Question {i+1} doit avoir exactement 4 options")
                
                if not isinstance(q_data["correct_answer"], int) or q_data["correct_answer"] not in [0, 1, 2, 3]:
                    raise Exception(f"Question {i+1}: correct_answer doit être 0, 1, 2 ou 3")
            
            # Créer le QCM
            qcm_id = str(uuid.uuid4())
            questions = []
            
            for i, q_data in enumerate(qcm_data["questions"]):
                question = QCMQuestion(
                    id=f"{qcm_id}_q{i}",
                    question=q_data["question"],
                    options=q_data["options"],
                    correct_answer=q_data["correct_answer"],
                    explanation=q_data["explanation"]
                )
                questions.append(question)
            
            qcm = QCM(
                id=qcm_id,
                title=qcm_data["title"],
                questions=questions,
                created_at=datetime.now(),
                based_on_documents=doc_names
            )
            
            # Stocker le QCM
            qcm_store.add_qcm(qcm)
            
            return {
                "success": True,
                "qcm": {
                    "id": qcm.id,
                    "title": qcm.title,
                    "questions": [
                        {
                            "id": q.id,
                            "question": q.question,
                            "options": q.options
                        } for q in qcm.questions
                    ],
                    "total_questions": len(qcm.questions)
                }
            }
            
        except Exception as e:
            print(f"Erreur lors de la génération par LLM: {str(e)}")
            print("Utilisation du QCM de fallback...")
            
            # Utiliser le QCM de fallback
            try:
                qcm_data = self.create_fallback_qcm(num_questions)
                
                # Créer le QCM avec les données de fallback
                qcm_id = str(uuid.uuid4())
                questions = []
                
                for i, q_data in enumerate(qcm_data["questions"]):
                    question = QCMQuestion(
                        id=f"{qcm_id}_q{i}",
                        question=q_data["question"],
                        options=q_data["options"],
                        correct_answer=q_data["correct_answer"],
                        explanation=q_data["explanation"]
                    )
                    questions.append(question)
                
                qcm = QCM(
                    id=qcm_id,
                    title=qcm_data["title"] + " (Mode démonstration)",
                    questions=questions,
                    created_at=datetime.now(),
                    based_on_documents=[]
                )
                
                # Stocker le QCM
                qcm_store.add_qcm(qcm)
                
                return {
                    "success": True,
                    "qcm": {
                        "id": qcm.id,
                        "title": qcm.title,
                        "questions": [
                            {
                                "id": q.id,
                                "question": q.question,
                                "options": q.options
                            } for q in qcm.questions
                        ],
                        "total_questions": len(qcm.questions)
                    }                }
                
            except Exception as fallback_error:
                return {
                    "success": False,
                    "error": f"Erreur lors de la génération du QCM et du fallback : {str(fallback_error)}"
                }
    
    def submit_qcm_answers(self, qcm_id: str, user_answers: List[int]) -> Dict[str, Any]:
        """Soumettre les réponses d'un QCM et calculer le score"""
        qcm = qcm_store.get_qcm(qcm_id)
        if not qcm:
            return {
                "success": False,
                "error": "QCM introuvable"
            }
        
        if len(user_answers) != len(qcm.questions):
            return {
                "success": False,
                "error": "Nombre de réponses incorrect"
            }
        
        # Calculer le score et les détails
        score = 0
        details = []
        
        for i, (user_answer, question) in enumerate(zip(user_answers, qcm.questions)):
            is_correct = user_answer == question.correct_answer
            if is_correct:
                score += 1
            
            details.append({
                "question_id": question.id,
                "question": question.question,
                "user_answer": user_answer,
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "options": question.options,
                "explanation": question.explanation
            })
          # Créer et stocker le résultat
        result = QCMResult(
            qcm_id=qcm_id,
            qcm_title=qcm.title,
            user_answers=user_answers,
            score=score,
            total_questions=len(qcm.questions),
            percentage=round((score / len(qcm.questions)) * 100, 1),
            details=details
        )
        qcm_store.add_result(result)
        
        # Mettre à jour les statistiques
        progress_store.update_progress_with_result(result)
        
        return {
            "success": True,
            "result": {
                "score": score,
                "total_questions": len(qcm.questions),
                "percentage": round((score / len(qcm.questions)) * 100, 1),
                "details": details
            }
        }
    
    def get_qcm_list(self) -> List[Dict[str, Any]]:
        """Récupérer la liste des QCM disponibles"""
        qcms = qcm_store.get_all_qcms()
        return [
            {
                "id": qcm.id,
                "title": qcm.title,
                "total_questions": len(qcm.questions),
                "created_at": qcm.created_at.isoformat(),
                "based_on_documents": qcm.based_on_documents
            }
            for qcm in qcms
        ]
    
    def get_qcm_by_id(self, qcm_id: str) -> Dict[str, Any]:
        """Récupérer un QCM par son ID pour le refaire"""
        qcm = qcm_store.get_qcm(qcm_id)
        if not qcm:
            return {
                "success": False,
                "error": "QCM introuvable"
            }
        
        return {
            "success": True,
            "qcm": {
                "id": qcm.id,
                "title": qcm.title,
                "questions": [
                    {
                        "id": q.id,
                        "question": q.question,
                        "options": q.options
                    } for q in qcm.questions
                ],
                "total_questions": len(qcm.questions)
            }
        }


# Instance globale du service QCM
qcm_service = QCMService()
