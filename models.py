"""
Modèles de données et stockage pour ChattuBottu
"""
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

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

# Instance globale du stockage
document_store = DocumentStore()
