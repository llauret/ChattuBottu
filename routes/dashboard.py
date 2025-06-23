"""
Routes pour le dashboard et les statistiques
"""
from flask import Blueprint, jsonify, request, render_template
from services.stats_service import stats_service
from datetime import datetime
from models import qcm_store, QCMResult

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/', methods=['GET'])
def dashboard_page():
    """Afficher la page dashboard complète"""
    try:
        # Récupérer toutes les données nécessaires
        stats = stats_service.get_dashboard_data()
        score_history = stats_service.get_score_history()
        activities = stats_service.get_recent_activities()
        recommendations = stats_service.get_recommendations()
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             score_history=score_history,
                             activities=activities,
                             recommendations=recommendations)
    except Exception as e:
        # En cas d'erreur, afficher le dashboard avec des données vides
        return render_template('dashboard.html', 
                             stats={}, 
                             score_history=[],
                             activities=[],
                             recommendations=[])


@dashboard_bp.route('/data', methods=['GET'])
def get_dashboard_data():
    """Récupérer les données principales du dashboard"""
    try:
        stats = stats_service.get_dashboard_data()
        score_history = stats_service.get_score_history()
        activities = stats_service.get_recent_activities()
        recommendations = stats_service.get_recommendations()        # Convertir les activités en un format sérialisable
        activities_list = [
            {
                "type": a.get('type', 'other'),
                "description": a.get('description', 'Activité'),
                "timestamp": a['timestamp'].isoformat() if isinstance(a.get('timestamp'), datetime) else a.get('timestamp'),
            }
            for a in activities
        ]
          # Ajout d'un log pour déboguer
        print("STATS:", stats)
        print("SCORE_HISTORY:", score_history)
        print("ACTIVITIES:", activities_list[:2] if activities_list else [])  # Pour limiter la taille du log
        print("RECOMMENDATIONS:", recommendations[:2] if recommendations else [])  # Pour limiter la taille du log
        
        data = {
            "stats": stats,
            "score_history": score_history,
            "activities": activities_list,
            "recommendations": recommendations,
        }
        
        return jsonify({"success": True, "data": data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la récupération des données : {str(e)}",
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
        required_fields = ['qcm_id', 'user_answers', 'score', 'total_questions', 'percentage', 'details', 'qcm_title']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Champ manquant : {field}"
                }), 400
        
        # Créer un objet QCMResult à partir des données reçues
        result = QCMResult(
            qcm_id=data['qcm_id'],
            qcm_title=data['qcm_title'],
            user_answers=data['user_answers'],
            score=data['score'],
            total_questions=data['total_questions'],
            percentage=data['percentage'],
            details=data['details'],
            completed_at=datetime.now()
        )
        
        # Le qcm_store doit aussi être mis à jour
        qcm_store.add_result(result)
        
        # Mettre à jour les statistiques
        stats_service.update_qcm_completion(result)
        
        return jsonify({
            "success": True,
            "message": "Statistiques QCM mises à jour"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la mise à jour : {str(e)}"
        }), 500
