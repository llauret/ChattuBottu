"""
Point d'entrée principal de l'application ChattuBottu
Architecture en Séparation des Responsabilités (SoC)
"""
from flask import Flask

# Import de la configuration
from config import config

# Import des blueprints (routes)
from routes.main import main_bp
from routes.chat import chat_bp
from routes.files import files_bp
from routes.qcm import qcm_bp

def create_app():
    """Factory pour créer l'application Flask"""
    app = Flask(__name__)
    
    # Configuration
    app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
    app.config['DEBUG'] = config.DEBUG
    app.config['SECRET_KEY'] = config.SECRET_KEY
      # Enregistrement des blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(qcm_bp)
    
    return app

def main():
    """Fonction principale"""
    app = create_app()
    app.run(debug=config.DEBUG)

if __name__ == "__main__":
    main()
