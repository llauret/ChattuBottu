"""
Routes pour la gestion des QCM
"""
from flask import Blueprint, request, jsonify
from services.qcm_service import qcm_service

qcm_bp = Blueprint('qcm', __name__, url_prefix='/qcm')

@qcm_bp.route('/generate', methods=['POST'])
def generate_qcm():
    """Générer un nouveau QCM"""
    data = request.get_json() or {}
    num_questions = data.get('num_questions', 5)
    
    # Validation du nombre de questions
    if not isinstance(num_questions, int) or num_questions < 1 or num_questions > 20:
        return jsonify({
            "success": False,
            "error": "Le nombre de questions doit être entre 1 et 20"
        }), 400
    
    result = qcm_service.generate_qcm(num_questions)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 400

@qcm_bp.route('/submit', methods=['POST'])
def submit_qcm():
    """Soumettre les réponses d'un QCM"""
    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "error": "Données manquantes"
        }), 400
    
    qcm_id = data.get('qcm_id')
    user_answers = data.get('answers')
    
    if not qcm_id or user_answers is None:
        return jsonify({
            "success": False,
            "error": "ID du QCM et réponses requis"
        }), 400
    
    result = qcm_service.submit_qcm_answers(qcm_id, user_answers)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 400

@qcm_bp.route('/list', methods=['GET'])
def list_qcms():
    """Récupérer la liste des QCM disponibles"""
    qcms = qcm_service.get_qcm_list()
    return jsonify({
        "success": True,
        "qcms": qcms
    })
