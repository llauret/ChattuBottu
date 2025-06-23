"""
Modèles de données et stockage pour ChattuBottu
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Document:
    """Représente un document ingéré"""
    filename: str
    content: str
    upload_date: datetime
    file_type: str
    size: int


class DocumentStore:
    """Stockage en mémoire des documents ingérés"""
    
    def __init__(self):
        self._documents: List[Document] = []
        self._ingested_content: List[str] = []
    
    def add_document(self, filename: str, content: str, file_type: str, size: int) -> None:
        """Ajouter un document au stockage"""
        document = Document(
            filename=filename,
            content=content,
            upload_date=datetime.now(),
            file_type=file_type,
            size=size
        )
        self._documents.append(document)
        self._ingested_content.append(content)
    
    def get_documents(self) -> List[Document]:
        """Récupérer tous les documents"""
        return self._documents.copy()
    
    def get_ingested_content(self) -> List[str]:
        """Récupérer le contenu ingéré pour le LLM"""
        return self._ingested_content.copy()
    
    def get_recent_content(self, limit: int = 3) -> str:
        """Récupérer le contenu récent pour le contexte"""
        recent = self._ingested_content[-limit:] if self._ingested_content else []
        return "\n\n".join(recent)
    
    def remove_document_by_filename(self, filename: str) -> bool:
        """Supprimer un document par nom de fichier"""
        for i, doc in enumerate(self._documents):
            if doc.filename == filename:
                del self._documents[i]
                if i < len(self._ingested_content):
                    del self._ingested_content[i]
                return True
        return False
    
    def has_documents(self) -> bool:
        """Vérifier s'il y a des documents ingérés"""
        return len(self._documents) > 0
    
    def clear(self) -> None:
        """Vider le stockage"""
        self._documents.clear()
        self._ingested_content.clear()


@dataclass 
class QCMQuestion:
    """Représente une question de QCM"""
    id: str
    question: str
    options: List[str]  # Les options de réponse (A, B, C, D)
    correct_answer: int  # Index de la bonne réponse (0, 1, 2, 3)
    explanation: str  # Explication de la réponse


@dataclass
class QCM:
    """Représente un QCM complet"""
    id: str
    title: str
    questions: List[QCMQuestion]
    created_at: datetime
    based_on_documents: List[str]  # Noms des documents utilisés


@dataclass
class QCMResult:
    """Résultat d'un QCM"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    qcm_id: str = ""
    qcm_title: str = ""
    user_answers: List[int] = field(default_factory=list)
    score: int = 0
    total_questions: int = 0
    percentage: float = 0.0
    completion_time: Optional[datetime] = None  # Temps de complétion
    completed_at: datetime = field(default_factory=datetime.now)
    details: List[dict] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)  # Thèmes abordés


@dataclass
class LearningSession:
    """Représente une session d'apprentissage"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # Durée en secondes
    activities: List[str] = field(default_factory=list)  # chat, qcm, mindmap, revision
    documents_consulted: List[str] = field(default_factory=list)
    qcm_results: List[str] = field(default_factory=list)  # IDs des résultats QCM


@dataclass
class UserProgress:
    """Progression de l'utilisateur"""
    user_id: str = "default"
    total_qcms_completed: int = 0
    total_questions_answered: int = 0
    total_correct_answers: int = 0
    overall_success_rate: float = 0.0
    time_spent_learning: float = 0.0  # En secondes
    themes_studied: Dict[str, int] = field(default_factory=dict)  # theme -> nb questions
    themes_success_rate: Dict[str, float] = field(default_factory=dict)  # theme -> %
    learning_streak: int = 0  # Nombre de jours consécutifs d'apprentissage
    last_activity: Optional[datetime] = None
    favorite_themes: List[str] = field(default_factory=list)
    weak_themes: List[str] = field(default_factory=list)


class ProgressStore:
    """Stockage des données de progression"""
    
    def __init__(self):
        self._sessions: List[LearningSession] = []
        self._progress: UserProgress = UserProgress()
        self._current_session: Optional[LearningSession] = None
    
    def start_session(self) -> str:
        """Démarrer une nouvelle session d'apprentissage"""
        self._current_session = LearningSession()
        self._sessions.append(self._current_session)
        return self._current_session.id
    
    def end_session(self) -> None:
        """Terminer la session actuelle"""
        if self._current_session:
            self._current_session.end_time = datetime.now()
            self._current_session.duration = (
                self._current_session.end_time - self._current_session.start_time
            ).total_seconds()
            self._progress.time_spent_learning += self._current_session.duration
            self._current_session = None
    
    def add_activity(self, activity: str, document: str = None) -> None:
        """Ajouter une activité à la session actuelle"""
        if self._current_session:
            self._current_session.activities.append(activity)
            if document:
                self._current_session.documents_consulted.append(document)
    
    def update_progress_with_result(self, result: QCMResult) -> None:
        """Mettre à jour la progression avec un résultat de QCM"""
        self._progress.total_qcms_completed += 1
        self._progress.total_questions_answered += result.total_questions
        self._progress.total_correct_answers += result.score
        self._progress.overall_success_rate = (
            self._progress.total_correct_answers / self._progress.total_questions_answered * 100
            if self._progress.total_questions_answered > 0 else 0
        )
        self._progress.last_activity = datetime.now()
        
        # Mettre à jour les statistiques par thème
        for theme in result.themes:
            if theme not in self._progress.themes_studied:
                self._progress.themes_studied[theme] = 0
                self._progress.themes_success_rate[theme] = 0
            
            theme_questions = len([d for d in result.details if theme in d.get('themes', [])])
            theme_correct = len([d for d in result.details if theme in d.get('themes', []) and d['is_correct']])
            
            self._progress.themes_studied[theme] += theme_questions
            total_theme_questions = self._progress.themes_studied[theme]
            
            # Recalculer le taux de succès pour ce thème
            if total_theme_questions > 0:
                self._progress.themes_success_rate[theme] = (
                    theme_correct / total_theme_questions * 100
                )
        
        # Identifier les thèmes faibles et favoris
        self._update_theme_preferences()
        
        if self._current_session:
            self._current_session.qcm_results.append(result.id)
    
    def _update_theme_preferences(self) -> None:
        """Mettre à jour les thèmes favoris et faibles"""
        if not self._progress.themes_success_rate:
            return
        
        sorted_themes = sorted(
            self._progress.themes_success_rate.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        self._progress.favorite_themes = [theme for theme, rate in sorted_themes[:3] if rate >= 70]
        self._progress.weak_themes = [theme for theme, rate in sorted_themes if rate < 50]
    
    def get_progress(self) -> UserProgress:
        """Récupérer la progression de l'utilisateur"""
        return self._progress
    
    def get_sessions(self) -> List[LearningSession]:
        """Récupérer toutes les sessions"""
        return self._sessions.copy()
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Récupérer les données pour le dashboard"""
        return {
            "overall_stats": {
                "total_qcms": self._progress.total_qcms_completed,
                "total_questions": self._progress.total_questions_answered,
                "success_rate": round(self._progress.overall_success_rate, 1),
                "time_spent": round(self._progress.time_spent_learning / 3600, 1),  # En heures
                "learning_streak": self._progress.learning_streak
            },
            "themes_stats": {
                "themes_studied": dict(self._progress.themes_studied),
                "themes_success_rate": {k: round(v, 1) for k, v in self._progress.themes_success_rate.items()},
                "favorite_themes": self._progress.favorite_themes,
                "weak_themes": self._progress.weak_themes
            },
            "recent_sessions": [
                {
                    "date": session.start_time.strftime("%Y-%m-%d"),
                    "duration": round(session.duration / 60, 1) if session.duration else 0,
                    "activities": session.activities,
                    "qcm_count": len(session.qcm_results)
                }
                for session in self._sessions[-10:]  # 10 dernières sessions
            ]
        }


class QCMStore:
    """Stockage des QCM et résultats"""
    
    def __init__(self):
        self._qcms: List[QCM] = []
        self._results: List[QCMResult] = []
    
    def add_qcm(self, qcm: QCM) -> None:
        """Ajouter un QCM"""
        self._qcms.append(qcm)
    
    def get_qcm(self, qcm_id: str) -> Optional[QCM]:
        """Récupérer un QCM par ID"""
        for qcm in self._qcms:
            if qcm.id == qcm_id:
                return qcm
        return None
    
    def get_all_qcms(self) -> List[QCM]:
        """Récupérer tous les QCM"""
        return self._qcms.copy()
    
    def add_result(self, result: QCMResult) -> None:
        """Ajouter un résultat de QCM"""
        self._results.append(result)
    
    def get_results_for_qcm(self, qcm_id: str) -> List[QCMResult]:
        """Récupérer les résultats d'un QCM"""
        return [r for r in self._results if r.qcm_id == qcm_id]
    
    def get_all_results(self) -> List[QCMResult]:
        """Récupérer tous les résultats"""
        return self._results.copy()


# Instances globales du stockage
document_store = DocumentStore()
qcm_store = QCMStore()
progress_store = ProgressStore()
