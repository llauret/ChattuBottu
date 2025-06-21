"""
Routes pour le dashboard et les statistiques
"""
from flask import Blueprint, jsonify, request
from services.stats_service import stats_service

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/data', methods=['GET'])
def get_dashboard_data():
    """Récupérer les données principales du dashboard"""
    try:
        data = stats_service.get_dashboard_data()
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la récupération des données : {str(e)}"
        }), 500


@dashboard_bp.route('/analytics', methods=['GET'])
def get_learning_analytics():
    """Récupérer les analytics avancées"""
    try:
        analytics = stats_service.get_learning_analytics()
        return jsonify({
            "success": True,
            "analytics": analytics
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la récupération des analytics : {str(e)}"
        }), 500


@dashboard_bp.route('/session/start', methods=['POST'])
def start_session():
    """Démarrer une session d'apprentissage"""
    try:
        session_id = stats_service.start_session()
        return jsonify({
            "success": True,
            "session_id": session_id
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors du démarrage de session : {str(e)}"
        }), 500


@dashboard_bp.route('/session/end', methods=['POST'])
def end_session():
    """Terminer une session d'apprentissage"""
    try:
        stats_service.end_session()
        return jsonify({
            "success": True,
            "message": "Session terminée avec succès"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la fin de session : {str(e)}"
        }), 500


@dashboard_bp.route('/activity', methods=['POST'])
def track_activity():
    """Enregistrer une activité"""
    try:
        data = request.get_json()
        activity = data.get('activity')
        document = data.get('document')
        
        if not activity:
            return jsonify({
                "success": False,
                "error": "L'activité est requise"
            }), 400
        
        stats_service.track_activity(activity, document)
        return jsonify({
            "success": True,
            "message": "Activité enregistrée"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de l'enregistrement : {str(e)}"
        }), 500


@dashboard_bp.route('/qcm/complete', methods=['POST'])
def complete_qcm():
    """Enregistrer la completion d'un QCM pour les statistiques"""
    try:
        data = request.get_json()
        required_fields = ['qcm_id', 'user_answers', 'score', 'total_questions']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Champ manquant : {field}"
                }), 400
        
        stats_service.update_qcm_completion(data)
        return jsonify({
            "success": True,
            "message": "Statistiques QCM mises à jour"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la mise à jour : {str(e)}"
        }), 500
