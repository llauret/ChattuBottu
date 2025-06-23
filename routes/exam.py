"""
Routes pour la gestion des examens complets
"""
from flask import Blueprint, request, jsonify, render_template
from services.exam_service import exam_service, exam_store

exam_bp = Blueprint('exam', __name__, url_prefix='/exam')


@exam_bp.route('/generate', methods=['POST'])
def generate_exam():
    """Générer un nouvel examen"""
    try:
        data = request.get_json()
        
        num_questions = data.get('num_questions', 20)
        duration_minutes = data.get('duration_minutes', 60)
        difficulty_level = data.get('difficulty_level', 'mixed')
        
        # Valider les paramètres
        if num_questions < 5 or num_questions > 50:
            return jsonify({
                "success": False,
                "error": "Le nombre de questions doit être entre 5 et 50"
            }), 400
        
        if duration_minutes < 15 or duration_minutes > 180:
            return jsonify({
                "success": False,
                "error": "La durée doit être entre 15 et 180 minutes"
            }), 400
        
        # Générer l'examen
        result = exam_service.generate_exam(
            num_questions=num_questions,
            duration_minutes=duration_minutes,
            difficulty_level=difficulty_level
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la génération de l'examen: {str(e)}"
        }), 500


@exam_bp.route('/list', methods=['GET'])
def list_exams():
    """Lister tous les examens disponibles"""
    try:
        exams = exam_store.get_all_exams()
        
        exam_list = []
        for exam in exams:
            # Obtenir les statistiques de base
            results = exam_store.get_results_for_exam(exam.id)
            
            exam_list.append({
                "id": exam.id,
                "title": exam.title,
                "total_questions": len(exam.questions),
                "duration_minutes": exam.duration_minutes,
                "total_points": exam.total_points,
                "created_at": exam.created_at.strftime('%d/%m/%Y à %H:%M'),
                "attempts": len(results),
                "based_on_documents": exam.based_on_documents
            })
        
        return jsonify({
            "success": True,
            "exams": exam_list
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la récupération des examens: {str(e)}"
        }), 500


@exam_bp.route('/<exam_id>', methods=['GET'])
def get_exam(exam_id):
    """Récupérer un examen spécifique pour le passer"""
    try:
        exam = exam_store.get_exam(exam_id)
        
        if not exam:
            return jsonify({
                "success": False,
                "error": "Examen introuvable"
            }), 404
        
        # Préparer les questions sans les réponses correctes
        questions = []
        for question in exam.questions:
            q_data = {
                "id": question.id,
                "question": question.question,
                "type": question.question_type,
                "points": question.points
            }
            
            if question.question_type in ['mcq', 'true_false']:
                q_data["options"] = question.options
            
            questions.append(q_data)
        
        return jsonify({
            "success": True,
            "exam": {
                "id": exam.id,
                "title": exam.title,
                "duration_minutes": exam.duration_minutes,
                "total_points": exam.total_points,
                "total_questions": len(exam.questions),
                "questions": questions,
                "instructions": [
                    "Lisez attentivement chaque question avant de répondre",
                    "Pour les questions à choix multiples, sélectionnez une seule réponse",
                    "Pour les questions Vrai/Faux, choisissez la réponse appropriée",
                    "Pour les questions à réponse courte, soyez précis et concis",
                    "Pour les questions de rédaction, développez votre réponse",
                    f"Vous avez {exam.duration_minutes} minutes pour terminer l'examen",
                    "Assurez-vous de sauvegarder vos réponses régulièrement"
                ]
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la récupération de l'examen: {str(e)}"
        }), 500


@exam_bp.route('/<exam_id>/submit', methods=['POST'])
def submit_exam(exam_id):
    """Soumettre les réponses d'un examen"""
    try:
        data = request.get_json()
        
        student_answers = data.get('answers', {})
        time_taken_minutes = data.get('time_taken_minutes', 0)
        
        if not student_answers:
            return jsonify({
                "success": False,
                "error": "Aucune réponse fournie"
            }), 400
        
        # Soumettre l'examen pour correction
        result = exam_service.submit_exam(
            exam_id=exam_id,
            student_answers=student_answers,
            time_taken_minutes=time_taken_minutes
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la soumission: {str(e)}"
        }), 500


@exam_bp.route('/result/<result_id>', methods=['GET'])
def get_exam_result(result_id):
    """Récupérer les résultats détaillés d'un examen"""
    try:
        result = exam_store.get_result(result_id)
        
        if not result:
            return jsonify({
                "success": False,
                "error": "Résultat introuvable"
            }), 404
        
        exam = exam_store.get_exam(result.exam_id)
        
        # Recalculer les détails pour l'affichage
        score_details = exam_service._calculate_score(exam, result.student_answers)
        
        return jsonify({
            "success": True,
            "result": {
                "id": result.id,
                "exam_title": exam.title if exam else "Examen supprimé",
                "score": result.score,
                "total_points": result.total_points,
                "percentage": (result.score / result.total_points) * 100,
                "passed": result.passed,
                "completed_at": result.completed_at.strftime('%d/%m/%Y à %H:%M'),
                "time_taken_minutes": result.time_taken_minutes,
                "question_details": score_details['question_details'],
                "summary": score_details['summary']
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la récupération du résultat: {str(e)}"
        }), 500


@exam_bp.route('/<exam_id>/statistics', methods=['GET'])
def get_exam_statistics(exam_id):
    """Obtenir les statistiques d'un examen"""
    try:
        stats = exam_service.get_exam_statistics(exam_id)
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la récupération des statistiques: {str(e)}"
        }), 500


@exam_bp.route('/page', methods=['GET'])
def exam_page():
    """Page d'interface pour les examens"""
    return render_template('exam.html')


@exam_bp.route('/<exam_id>/take', methods=['GET'])
def take_exam_page(exam_id):
    """Page pour passer un examen"""
    try:
        exam = exam_store.get_exam(exam_id)
        
        if not exam:
            return render_template('error.html', 
                                 error="Examen introuvable"), 404
        
        return render_template('take_exam.html', exam_id=exam_id)
        
    except Exception as e:
        return render_template('error.html', 
                             error=f"Erreur: {str(e)}"), 500


@exam_bp.route('/result/<result_id>/view', methods=['GET'])
def view_result_page(result_id):
    """Page pour voir les résultats d'un examen"""
    try:
        result = exam_store.get_result(result_id)
        
        if not result:
            return render_template('error.html', 
                                 error="Résultat introuvable"), 404
        
        return render_template('exam_result.html', result_id=result_id)
        
    except Exception as e:
        return render_template('error.html', 
                             error=f"Erreur: {str(e)}"), 500
