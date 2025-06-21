"""
Service de gestion des fichiers pour ChattuBottu
"""
import os
import mimetypes
import re
from collections import Counter
from typing import Tuple, Optional
from werkzeug.utils import secure_filename

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

from config import config
from models import document_store

class FileService:
    """Service pour la gestion des fichiers et l'ingestion de documents"""
    
    def __init__(self):
        self.upload_folder = config.UPLOAD_FOLDER
        self.max_bow_words = config.MAX_BOW_WORDS
        self.max_text_length = config.MAX_TEXT_LENGTH
    
    def extract_text_from_pdf(self, filepath: str) -> str:
        """Extraire le texte d'un fichier PDF"""
        if not PdfReader:
            return "[Erreur: PyPDF2 non installé]"
        
        try:
            reader = PdfReader(filepath)
            text = " ".join(page.extract_text() or "" for page in reader.pages)
            return text
        except Exception as e:
            return f"[Erreur extraction PDF: {e}]"
    
    def summarize_text_bow(self, text: str, max_words: Optional[int] = None) -> str:
        """Résumer un texte avec la méthode Bag of Words"""
        if max_words is None:
            max_words = self.max_bow_words
        
        # Nettoyage et découpage
        words = re.findall(r"\b\w+\b", text.lower())
        counter = Counter(words)
        most_common = counter.most_common(max_words)
        bow = " ".join([f"{w}:{c}" for w, c in most_common])
        return f"BagOfWords résumé (top {max_words}):\n" + bow
    
    def ingest_file(self, filepath: str) -> None:
        """Ingérer un fichier dans le système"""
        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)
        mime, _ = mimetypes.guess_type(filepath)
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == ".pdf" or (mime and "pdf" in mime):
            # Traitement PDF
            text = self.extract_text_from_pdf(filepath)
            content = self.summarize_text_bow(text, self.max_bow_words)
            file_type = "pdf"
        else:
            # Traitement fichier texte
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Résumer si trop long
                if len(content) > self.max_text_length:
                    content = self.summarize_text_bow(content, self.max_bow_words)
            file_type = ext.lstrip('.')
        
        # Ajouter au stockage
        document_store.add_document(filename, content, file_type, file_size)
    
    def save_uploaded_file(self, file) -> Tuple[bool, str, Optional[str]]:
        """Sauvegarder un fichier uploadé"""
        if not file or file.filename == '':
            return False, "Aucun fichier sélectionné", None
        
        filename = secure_filename(file.filename)
        if not filename:
            return False, "Nom de fichier invalide", None
        
        filepath = os.path.join(self.upload_folder, filename)
        
        try:
            file.save(filepath)
            return True, "Fichier sauvegardé avec succès", filepath
        except Exception as e:
            return False, f"Erreur lors de la sauvegarde : {e}", None
    
    def delete_file(self, filename: str) -> Tuple[bool, str]:
        """Supprimer un fichier"""
        if not filename:
            return False, "Aucun nom de fichier fourni"
        
        # Sécuriser le nom de fichier
        safe_filename = secure_filename(filename)
        filepath = os.path.join(self.upload_folder, safe_filename)
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                # Supprimer aussi du stockage des documents
                document_store.remove_document_by_filename(filename)
                return True, "Fichier supprimé avec succès"
            else:
                return False, "Fichier introuvable"
        except Exception as e:
            return False, f"Erreur lors de la suppression : {e}"
    
    def list_pdf_files(self) -> list:
        """Lister tous les fichiers PDF dans le dossier d'upload"""
        try:
            files = []
            for filename in os.listdir(self.upload_folder):
                if filename.lower().endswith('.pdf'):
                    files.append(filename)
            return files
        except Exception:
            return []
    
    def get_file_info(self, filename: str) -> Optional[dict]:
        """Obtenir les informations d'un fichier"""
        filepath = os.path.join(self.upload_folder, secure_filename(filename))
        
        if not os.path.exists(filepath):
            return None
        
        stat = os.stat(filepath)
        return {
            'filename': filename,
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'path': filepath
        }

# Instance globale du service de fichiers
file_service = FileService()
