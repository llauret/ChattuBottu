"""
Routes pour la gestion des fichiers
"""
from flask import Blueprint, request, jsonify

from services.file_service import file_service

files_bp = Blueprint('files', __name__)

@files_bp.route("/upload", methods=["POST"])
def upload_file():
    """Upload et ingestion de fichiers"""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Aucun fichier reçu."})
    
    files = request.files.getlist('file')
    saved_files = []
    errors = []
    
    for file in files:
        if file.filename == '':
            continue
        
        # Sauvegarder le fichier
        success, message, filepath = file_service.save_uploaded_file(file)
        
        if success and filepath:
            try:
                # Ingestion du fichier
                file_service.ingest_file(filepath)
                saved_files.append(file.filename)
            except Exception as e:
                errors.append(f"Erreur lors de l'ingestion de {file.filename}: {e}")
        else:
            errors.append(f"Erreur pour {file.filename}: {message}")
    
    if saved_files:
        response = {"success": True, "files": saved_files}
        if errors:
            response["warnings"] = errors
        return jsonify(response)
    else:
        return jsonify({
            "success": False, 
            "error": "Aucun fichier sauvegardé.",
            "details": errors
        })

@files_bp.route("/list_pdfs")
def list_pdfs():
    """Lister les fichiers PDF"""
    pdfs = file_service.list_pdf_files()
    return jsonify({"pdfs": pdfs})

@files_bp.route("/delete_pdf", methods=["POST"])
def delete_pdf():
    """Supprimer un fichier PDF"""
    data = request.get_json()
    filename = data.get('filename') if data else None
    
    if not filename:
        return jsonify({"success": False, "error": "Aucun nom de fichier fourni."})
    
    success, message = file_service.delete_file(filename)
    
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "error": message})
