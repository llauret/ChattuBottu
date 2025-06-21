"""
Configuration et variables d'environnement pour ChattuBottu
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Si python-dotenv n'est pas installé, on continue sans
    pass

class Config:
    """Configuration de l'application"""
    
    # Flask
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    
    # LLM
    MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', 'PgTNW3ULXTouUq0ZjgNlWk3DQTPDHRTz')
    MISTRAL_MODEL = os.getenv('MISTRAL_MODEL', 'mistral-large-latest')
    MISTRAL_TEMPERATURE = float(os.getenv('MISTRAL_TEMPERATURE', '0'))
    
    # Document processing
    MAX_BOW_WORDS = int(os.getenv('MAX_BOW_WORDS', '200'))
    MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', '8000'))
    
    def __init__(self):
        # Créer le dossier d'upload s'il n'existe pas
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)

# Instance globale de la configuration
config = Config()
