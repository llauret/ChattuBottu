"""
Routes pour les interactions avec le chatbot
"""
from flask import Blueprint, request, jsonify

from services.llm_service import llm_service

chat_bp = Blueprint('chat', __name__)

@chat_bp.route("/get")
def get_bot_response():
    """Obtenir une réponse du chatbot"""
    user_text = request.args.get('msg', '')
    if not user_text:
        return jsonify({"error": "Aucun message fourni"}), 400
    
    response = llm_service.get_chatbot_response(user_text)
    return response

@chat_bp.route("/generate_mindmap", methods=["POST"])
def generate_mindmap():
    """Générer une mindmap"""
    data = request.get_json()
    question = data.get("question", "") if data else ""
    
    if not question:
        return jsonify({"success": False, "error": "Aucune question fournie."}), 400
    
    markdown = llm_service.generate_mindmap_markdown(question)
    return jsonify({"success": True, "markdown": markdown})

@chat_bp.route("/generate_revision_sheet", methods=["POST"])
def generate_revision_sheet_route():
    """Générer une fiche de révision"""
    revision_sheet = llm_service.generate_revision_sheet()
    return jsonify({"success": True, "content": revision_sheet})
