"""
Service de gestion des examens complets avec génération intelligente de questions
"""
import json
import uuid
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from models import QCM, QCMQuestion, QCMResult, qcm_store, document_store, progress_store
from services.llm_service import llm_service
from services.qcm_service import clean_and_parse_json


class ExamQuestion:
    def __init__(self, id: str, question: str, question_type: str, options: List[str] = None, 
                 correct_answer: Any = None, points: int = 1, explanation: str = ""):
        self.id = id
        self.question = question
        self.question_type = question_type  # 'mcq', 'true_false', 'short_answer', 'essay'
        self.options = options or []
        self.correct_answer = correct_answer
        self.points = points
        self.explanation = explanation


class Exam:
    def __init__(self, id: str, title: str, questions: List[ExamQuestion], 
                 duration_minutes: int = 60, total_points: int = 100, 
                 created_at: datetime = None, based_on_documents: List[str] = None):
        self.id = id
        self.title = title
        self.questions = questions
        self.duration_minutes = duration_minutes
        self.total_points = total_points
        self.created_at = created_at or datetime.now()
        self.based_on_documents = based_on_documents or []


class ExamResult:
    def __init__(self, id: str, exam_id: str, student_answers: Dict[str, Any], 
                 score: float, total_points: int, passed: bool, 
                 completed_at: datetime = None, time_taken_minutes: int = 0):
        self.id = id
        self.exam_id = exam_id
        self.student_answers = student_answers
        self.score = score
        self.total_points = total_points
        self.passed = passed
        self.completed_at = completed_at or datetime.now()
        self.time_taken_minutes = time_taken_minutes


class ExamStore:
    def __init__(self):
        self.exams: Dict[str, Exam] = {}
        self.results: Dict[str, ExamResult] = {}
    
    def add_exam(self, exam: Exam):
        self.exams[exam.id] = exam
    
    def get_exam(self, exam_id: str) -> Optional[Exam]:
        return self.exams.get(exam_id)
    
    def get_all_exams(self) -> List[Exam]:
        return list(self.exams.values())
    
    def add_result(self, result: ExamResult):
        self.results[result.id] = result
    
    def get_result(self, result_id: str) -> Optional[ExamResult]:
        return self.results.get(result_id)
    
    def get_results_for_exam(self, exam_id: str) -> List[ExamResult]:
        return [r for r in self.results.values() if r.exam_id == exam_id]


# Instance globale
exam_store = ExamStore()


class ExamService:
    """Service pour gérer les examens complets avec génération intelligente"""
    
    def generate_exam(self, num_questions: int = 20, duration_minutes: int = 60, 
                     difficulty_level: str = "mixed") -> Dict[str, Any]:
        """Générer un examen complet avec différents types de questions"""
        
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
            
            # Répartition des types de questions
            question_distribution = self._get_question_distribution(num_questions)
            
            # Générer les questions par type
            all_questions = []
            total_points = 0
            
            # Questions à choix multiples (MCQ)
            if question_distribution['mcq'] > 0:
                mcq_questions = self._generate_mcq_questions(
                    context, question_distribution['mcq'], difficulty_level
                )
                all_questions.extend(mcq_questions)
                total_points += sum(q.points for q in mcq_questions)
            
            # Questions Vrai/Faux
            if question_distribution['true_false'] > 0:
                tf_questions = self._generate_true_false_questions(
                    context, question_distribution['true_false'], difficulty_level
                )
                all_questions.extend(tf_questions)
                total_points += sum(q.points for q in tf_questions)
            
            # Questions à réponse courte
            if question_distribution['short_answer'] > 0:
                sa_questions = self._generate_short_answer_questions(
                    context, question_distribution['short_answer'], difficulty_level
                )
                all_questions.extend(sa_questions)
                total_points += sum(q.points for q in sa_questions)
            
            # Questions de rédaction
            if question_distribution['essay'] > 0:
                essay_questions = self._generate_essay_questions(
                    context, question_distribution['essay'], difficulty_level
                )
                all_questions.extend(essay_questions)
                total_points += sum(q.points for q in essay_questions)
            
            # Mélanger les questions
            random.shuffle(all_questions)
            
            # Créer l'examen
            exam_id = str(uuid.uuid4())
            exam = Exam(
                id=exam_id,
                title=f"Examen complet - {datetime.now().strftime('%d/%m/%Y')}",
                questions=all_questions,
                duration_minutes=duration_minutes,
                total_points=total_points,
                based_on_documents=doc_names
            )
            
            # Stocker l'examen
            exam_store.add_exam(exam)
            
            return {
                "success": True,
                "exam": {
                    "id": exam.id,
                    "title": exam.title,
                    "duration_minutes": exam.duration_minutes,
                    "total_points": exam.total_points,
                    "questions": [
                        {
                            "id": q.id,
                            "question": q.question,
                            "type": q.question_type,
                            "options": q.options,
                            "points": q.points
                        } for q in exam.questions
                    ],
                    "total_questions": len(exam.questions)
                }
            }
            
        except Exception as e:
            print(f"Erreur lors de la génération de l'examen: {str(e)}")
            return {
                "success": False,
                "error": f"Erreur lors de la génération de l'examen: {str(e)}"
            }
    
    def _get_question_distribution(self, total_questions: int) -> Dict[str, int]:
        """Répartir les questions par type"""
        if total_questions <= 10:
            return {
                'mcq': total_questions,
                'true_false': 0,
                'short_answer': 0,
                'essay': 0
            }
        elif total_questions <= 20:
            return {
                'mcq': int(total_questions * 0.6),
                'true_false': int(total_questions * 0.3),
                'short_answer': int(total_questions * 0.1),
                'essay': 0
            }
        else:
            return {
                'mcq': int(total_questions * 0.5),
                'true_false': int(total_questions * 0.25),
                'short_answer': int(total_questions * 0.15),
                'essay': int(total_questions * 0.1)
            }
    
    def _generate_mcq_questions(self, context: str, num_questions: int, 
                               difficulty: str) -> List[ExamQuestion]:
        """Générer des questions à choix multiples intelligentes"""
        try:
            prompt = f"""Tu es un assistant pédagogique expert. À partir du contenu fourni, génère {num_questions} questions à choix multiples de niveau {difficulty}.

IMPORTANT: Tu dois retourner UNIQUEMENT un JSON valide, sans aucun texte avant ou après.

RÈGLES STRICTES POUR LES QUESTIONS :
- INTERDICTION totale de poser des questions sur le comptage de mots, d'occurrences ou de fréquences
- INTERDICTION de demander combien de fois un terme apparaît dans le document
- INTERDICTION de questions sur la structure du document, sa pagination ou sa mise en forme
- INTERDICTION de questions triviales sur des détails sans importance
- FOCUS sur la COMPRÉHENSION des concepts, des idées principales et des relations
- Poser des questions sur les définitions, les processus, les causes et effets
- Tester l'analyse, la synthèse et l'application des connaissances
- Questions sur les exemples concrets et leur interprétation
- Questions sur les avantages, inconvénients, et applications pratiques

Structure JSON requise :
{{
    "questions": [
        {{
            "question": "Quel est le principe fondamental de... ?",
            "options": ["Réponse A", "Réponse B", "Réponse C", "Réponse D"],
            "correct_answer": 0,
            "explanation": "La réponse A est correcte car...",
            "points": 2
        }}
    ]
}}

Règles techniques :
- Niveau de difficulté : {difficulty}
- 4 options par question (toutes plausibles mais une seule correcte)
- correct_answer: 0-3 (0=A, 1=B, 2=C, 3=D)
- Points selon difficulté: facile=1, moyen=2, difficile=3

EXEMPLES DE BONNES QUESTIONS :
- "Quel est l'objectif principal de cette méthode ?"
- "Dans quel contexte cette approche est-elle recommandée ?"
- "Quelle est la différence entre X et Y selon le document ?"
- "Quels sont les avantages de cette technique ?"
- "Comment cette méthode améliore-t-elle les performances ?"

Contenu à analyser : {context[:2500]}"""

            response = llm_service.get_completion(prompt)
            data = clean_and_parse_json(response)
            
            questions = []
            for i, q_data in enumerate(data["questions"]):
                points = 1 if difficulty == 'easy' else 2 if difficulty == 'medium' else 3
                question = ExamQuestion(
                    id=f"mcq_{i}_{uuid.uuid4()}",
                    question=q_data["question"],
                    question_type="mcq",
                    options=q_data["options"],
                    correct_answer=q_data["correct_answer"],
                    points=q_data.get("points", points),
                    explanation=q_data["explanation"]
                )
                questions.append(question)
            
            return questions
            
        except Exception as e:
            print(f"Erreur génération MCQ: {e}")
            return self._create_fallback_mcq_questions(num_questions)
    
    def _generate_true_false_questions(self, context: str, num_questions: int, 
                                     difficulty: str) -> List[ExamQuestion]:
        """Générer des questions Vrai/Faux intelligentes"""
        try:
            prompt = f"""À partir du contenu fourni, génère {num_questions} questions Vrai/Faux de niveau {difficulty}.

IMPORTANT: Retourne UNIQUEMENT un JSON valide.

RÈGLES STRICTES POUR LES QUESTIONS :
- INTERDICTION de questions sur le comptage ou les statistiques du document
- INTERDICTION de questions sur la structure ou la forme du document
- FOCUS sur la COMPRÉHENSION et la VALIDATION des concepts
- Créer des affirmations précises à évaluer sur la véracité des informations
- Tester la compréhension des principes et des relations
- Questions sur les définitions et les caractéristiques importantes
- Éviter les affirmations ambiguës ou subjectives

Structure JSON :
{{
    "questions": [
        {{
            "question": "Cette méthode permet d'améliorer significativement les performances dans tous les cas",
            "correct_answer": false,
            "explanation": "Explication claire de pourquoi c'est vrai ou faux",
            "points": 1
        }}
    ]
}}

EXEMPLES DE BONNES QUESTIONS VRAI/FAUX :
- "Cette approche est recommandée uniquement pour les situations complexes"
- "Le principe X est considéré comme fondamental dans cette méthode"
- "Cette technique présente des avantages dans tous les contextes d'application"
- "La mise en œuvre de cette solution nécessite des compétences spécialisées"

Contenu : {context[:2000]}"""

            response = llm_service.get_completion(prompt)
            data = clean_and_parse_json(response)
            
            questions = []
            for i, q_data in enumerate(data["questions"]):
                question = ExamQuestion(
                    id=f"tf_{i}_{uuid.uuid4()}",
                    question=q_data["question"],
                    question_type="true_false",
                    options=["Vrai", "Faux"],
                    correct_answer=0 if q_data["correct_answer"] else 1,
                    points=q_data.get("points", 1),
                    explanation=q_data["explanation"]
                )
                questions.append(question)
            
            return questions
            
        except Exception as e:
            print(f"Erreur génération Vrai/Faux: {e}")
            return self._create_fallback_tf_questions(num_questions)
    
    def _generate_short_answer_questions(self, context: str, num_questions: int, 
                                       difficulty: str) -> List[ExamQuestion]:
        """Générer des questions à réponse courte"""
        try:
            prompt = f"""À partir du contenu fourni, génère {num_questions} questions à réponse courte de niveau {difficulty}.

IMPORTANT: Retourne UNIQUEMENT un JSON valide.

RÈGLES POUR LES QUESTIONS :
- Questions nécessitant une réponse précise en quelques mots ou phrases
- Tester la connaissance des termes techniques et définitions
- Questions sur les étapes de processus ou méthodes
- Éviter les questions trop ouvertes ou subjectives

Structure JSON :
{{
    "questions": [
        {{
            "question": "Définissez en quelques mots le concept principal de...",
            "correct_answer": "Réponse attendue précise",
            "explanation": "Explication détaillée",
            "points": 3
        }}
    ]
}}

Contenu : {context[:2000]}"""

            response = llm_service.get_completion(prompt)
            data = clean_and_parse_json(response)
            
            questions = []
            for i, q_data in enumerate(data["questions"]):
                question = ExamQuestion(
                    id=f"sa_{i}_{uuid.uuid4()}",
                    question=q_data["question"],
                    question_type="short_answer",
                    correct_answer=q_data["correct_answer"],
                    points=q_data.get("points", 3),
                    explanation=q_data["explanation"]
                )
                questions.append(question)
            
            return questions
            
        except Exception as e:
            print(f"Erreur génération réponses courtes: {e}")
            return []
    
    def _generate_essay_questions(self, context: str, num_questions: int, 
                                difficulty: str) -> List[ExamQuestion]:
        """Générer des questions de rédaction"""
        try:
            prompt = f"""À partir du contenu fourni, génère {num_questions} questions de rédaction de niveau {difficulty}.

IMPORTANT: Retourne UNIQUEMENT un JSON valide.

Structure JSON :
{{
    "questions": [
        {{
            "question": "Analysez et expliquez l'importance de... en développant votre argumentation",
            "correct_answer": "Éléments clés attendus dans la réponse",
            "explanation": "Critères d'évaluation",
            "points": 5
        }}
    ]
}}

Contenu : {context[:2000]}"""

            response = llm_service.get_completion(prompt)
            data = clean_and_parse_json(response)
            
            questions = []
            for i, q_data in enumerate(data["questions"]):
                question = ExamQuestion(
                    id=f"essay_{i}_{uuid.uuid4()}",
                    question=q_data["question"],
                    question_type="essay",
                    correct_answer=q_data["correct_answer"],
                    points=q_data.get("points", 5),
                    explanation=q_data["explanation"]
                )
                questions.append(question)
            
            return questions
            
        except Exception as e:
            print(f"Erreur génération questions rédaction: {e}")
            return []
    
    def _create_fallback_mcq_questions(self, num_questions: int) -> List[ExamQuestion]:
        """Questions MCQ de fallback intelligentes"""
        fallback_questions = [
            {
                "question": "Quel est l'objectif principal de l'analyse de documents dans un système intelligent ?",
                "options": ["Stockage simple", "Compréhension du contenu", "Compression des données", "Archivage"],
                "correct_answer": 1,
                "explanation": "L'analyse vise à comprendre et extraire le sens du contenu pour permettre des interactions intelligentes."
            },
            {
                "question": "Quelle approche est la plus efficace pour traiter des documents complexes ?",
                "options": ["Lecture séquentielle", "Analyse structurée avec IA", "Survol rapide", "Mémorisation brute"],
                "correct_answer": 1,
                "explanation": "L'analyse structurée avec IA permet une compréhension approfondie et une extraction d'informations pertinentes."
            },
            {
                "question": "Dans quel contexte l'automatisation de l'analyse documentaire est-elle particulièrement utile ?",
                "options": ["Documents simples", "Volumes importants de données", "Textes courts", "Images uniquement"],
                "correct_answer": 1,
                "explanation": "L'automatisation est cruciale pour traiter efficacement de gros volumes de documents complexes."
            }
        ]
        
        questions = []
        for i in range(min(num_questions, len(fallback_questions))):
            q_data = fallback_questions[i]
            question = ExamQuestion(
                id=f"fallback_mcq_{i}",
                question=q_data["question"],
                question_type="mcq",
                options=q_data["options"],
                correct_answer=q_data["correct_answer"],
                points=2,
                explanation=q_data["explanation"]
            )
            questions.append(question)
        
        return questions
    
    def _create_fallback_tf_questions(self, num_questions: int) -> List[ExamQuestion]:
        """Questions Vrai/Faux de fallback intelligentes"""
        fallback_questions = [
            {
                "question": "L'analyse automatique de documents nécessite une approche méthodique et structurée",
                "correct_answer": True,
                "explanation": "Une approche méthodique est essentielle pour obtenir des résultats fiables et pertinents."
            },
            {
                "question": "Tous les documents ont exactement la même structure et peuvent être traités de manière identique",
                "correct_answer": False,
                "explanation": "Les documents varient considérablement en structure, format et contenu, nécessitant des approches adaptées."
            },
            {
                "question": "L'intelligence artificielle peut améliorer significativement la compréhension des documents complexes",
                "correct_answer": True,
                "explanation": "L'IA permet d'analyser, comprendre et extraire des informations de manière plus sophistiquée que les méthodes traditionnelles."
            }
        ]
        
        questions = []
        for i in range(min(num_questions, len(fallback_questions))):
            q_data = fallback_questions[i]
            question = ExamQuestion(
                id=f"fallback_tf_{i}",
                question=q_data["question"],
                question_type="true_false",
                options=["Vrai", "Faux"],
                correct_answer=0 if q_data["correct_answer"] else 1,
                points=1,
                explanation=q_data["explanation"]
            )
            questions.append(question)
        
        return questions
    
    def submit_exam(self, exam_id: str, student_answers: Dict[str, Any], 
                   time_taken_minutes: int = 0) -> Dict[str, Any]:
        """Soumettre un examen et obtenir la correction automatique"""
        
        exam = exam_store.get_exam(exam_id)
        if not exam:
            return {
                "success": False,
                "error": "Examen introuvable"
            }
        
        try:
            # Calculer le score
            score_details = self._calculate_score(exam, student_answers)
            
            # Créer le résultat
            result_id = str(uuid.uuid4())
            result = ExamResult(
                id=result_id,
                exam_id=exam_id,
                student_answers=student_answers,
                score=score_details['score'],
                total_points=exam.total_points,
                passed=score_details['passed'],
                time_taken_minutes=time_taken_minutes
            )
            
            # Stocker le résultat
            exam_store.add_result(result)
            
            return {
                "success": True,
                "result": {
                    "id": result.id,
                    "score": result.score,
                    "total_points": result.total_points,
                    "percentage": (result.score / result.total_points) * 100,
                    "passed": result.passed,
                    "time_taken_minutes": result.time_taken_minutes,
                    "question_details": score_details['question_details'],
                    "summary": score_details['summary']
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur lors de la correction: {str(e)}"
            }
    
    def _calculate_score(self, exam: Exam, student_answers: Dict[str, Any]) -> Dict[str, Any]:
        """Calculer le score et les détails de correction"""
        
        total_score = 0
        max_score = 0
        question_details = []
        
        for question in exam.questions:
            max_score += question.points
            student_answer = student_answers.get(question.id)
            
            if question.question_type in ['mcq', 'true_false']:
                # Questions à choix multiples et vrai/faux
                is_correct = student_answer == question.correct_answer
                points_earned = question.points if is_correct else 0
                
            elif question.question_type == 'short_answer':
                # Questions à réponse courte - comparaison flexible
                points_earned = self._score_short_answer(
                    student_answer, question.correct_answer, question.points
                )
                is_correct = points_earned > 0
                
            elif question.question_type == 'essay':
                # Questions de rédaction - évaluation par mots-clés
                points_earned = self._score_essay(
                    student_answer, question.correct_answer, question.points
                )
                is_correct = points_earned > question.points * 0.5
                
            else:
                points_earned = 0
                is_correct = False
            
            total_score += points_earned
            
            question_details.append({
                "question_id": question.id,
                "question": question.question,
                "student_answer": student_answer,
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "points_earned": points_earned,
                "max_points": question.points,
                "explanation": question.explanation
            })
        
        # Seuil de réussite à 60%
        passing_threshold = max_score * 0.6
        passed = total_score >= passing_threshold
        
        return {
            "score": total_score,
            "passed": passed,
            "question_details": question_details,
            "summary": {
                "total_questions": len(exam.questions),
                "correct_answers": sum(1 for q in question_details if q["is_correct"]),
                "percentage": (total_score / max_score) * 100 if max_score > 0 else 0,
                "passing_threshold": passing_threshold
            }
        }
    
    def _score_short_answer(self, student_answer: str, correct_answer: str, max_points: int) -> int:
        """Scorer une réponse courte"""
        if not student_answer or not correct_answer:
            return 0
        
        student_answer = student_answer.lower().strip()
        correct_answer = correct_answer.lower().strip()
        
        # Correspondance exacte
        if student_answer == correct_answer:
            return max_points
        
        # Correspondance partielle (mots-clés)
        correct_words = set(correct_answer.split())
        student_words = set(student_answer.split())
        
        if len(correct_words) == 0:
            return 0
        
        overlap = len(correct_words.intersection(student_words))
        similarity = overlap / len(correct_words)
        
        if similarity >= 0.8:
            return max_points
        elif similarity >= 0.6:
            return int(max_points * 0.7)
        elif similarity >= 0.4:
            return int(max_points * 0.5)
        else:
            return 0
    
    def _score_essay(self, student_answer: str, expected_elements: str, max_points: int) -> int:
        """Scorer une question de rédaction"""
        if not student_answer or not expected_elements:
            return 0
        
        student_answer = student_answer.lower()
        expected_elements = expected_elements.lower()
        
        # Extraire les mots-clés attendus
        expected_keywords = set(expected_elements.split())
        student_words = set(student_answer.split())
        
        if len(expected_keywords) == 0:
            return int(max_points * 0.5)  # Score par défaut si pas de critères
        
        # Calculer la présence des mots-clés
        keyword_overlap = len(expected_keywords.intersection(student_words))
        keyword_score = keyword_overlap / len(expected_keywords)
        
        # Facteur de longueur (encourager les réponses développées)
        length_factor = min(len(student_answer.split()) / 50, 1.0)  # Optimal à 50 mots
        
        # Score final
        final_score = (keyword_score * 0.7 + length_factor * 0.3) * max_points
        
        return int(final_score)
    
    def get_exam_statistics(self, exam_id: str) -> Dict[str, Any]:
        """Obtenir les statistiques d'un examen"""
        
        exam = exam_store.get_exam(exam_id)
        if not exam:
            return {"success": False, "error": "Examen introuvable"}
        
        results = exam_store.get_results_for_exam(exam_id)
        
        if not results:
            return {
                "success": True,
                "statistics": {
                    "total_attempts": 0,
                    "average_score": 0,
                    "pass_rate": 0,
                    "question_analysis": []
                }
            }
        
        # Calculer les statistiques
        scores = [r.score for r in results]
        percentages = [(r.score / r.total_points) * 100 for r in results]
        
        statistics = {
            "total_attempts": len(results),
            "average_score": sum(scores) / len(scores),
            "average_percentage": sum(percentages) / len(percentages),
            "pass_rate": (sum(1 for r in results if r.passed) / len(results)) * 100,
            "min_score": min(scores),
            "max_score": max(scores),
            "question_analysis": self._analyze_questions(exam, results)
        }
        
        return {
            "success": True,
            "statistics": statistics
        }
    
    def _analyze_questions(self, exam: Exam, results: List[ExamResult]) -> List[Dict[str, Any]]:
        """Analyser les performances par question"""
        question_stats = []
        
        for question in exam.questions:
            correct_count = 0
            total_count = 0
            
            for result in results:
                if question.id in result.student_answers:
                    total_count += 1
                    # Logique simplifiée pour déterminer si correct
                    student_answer = result.student_answers[question.id]
                    if question.question_type in ['mcq', 'true_false']:
                        if student_answer == question.correct_answer:
                            correct_count += 1
                    # Pour les autres types, on considère que c'est correct si > 50% des points
            
            success_rate = (correct_count / total_count * 100) if total_count > 0 else 0
            
            question_stats.append({
                "question_id": question.id,
                "question": question.question[:100] + "..." if len(question.question) > 100 else question.question,
                "type": question.question_type,
                "success_rate": success_rate,
                "total_attempts": total_count
            })
        
        return question_stats


# Instance globale du service
exam_service = ExamService()
