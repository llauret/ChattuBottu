"""
Service de gestion des statistiques et du dashboard
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import time

from models import progress_store, qcm_store, QCMResult


class StatsService:
    """Service pour gérer les statistiques et le dashboard"""
    
    def __init__(self):
        self._session_start_time = None
    
    def start_session(self) -> str:
        """Démarrer une session d'apprentissage"""
        self._session_start_time = time.time()
        return progress_store.start_session()
    
    def end_session(self) -> None:
        """Terminer la session d'apprentissage"""
        progress_store.end_session()
        self._session_start_time = None
    
    def track_activity(self, activity: str, document: str = None) -> None:
        """Enregistrer une activité"""
        progress_store.add_activity(activity, document)
    
    def update_qcm_completion(self, result: 'QCMResult') -> None:
        """Mettre à jour les statistiques après un QCM"""
        # Extraire les thèmes depuis le titre du QCM (simple extraction)
        themes = self._extract_themes_from_title(result.qcm_title)
        
        result.themes = themes
        
        # Ajouter les thèmes aux détails des questions
        for detail in result.details:
            detail['themes'] = themes
        
        progress_store.update_progress_with_result(result)
    
    def _extract_themes_from_title(self, title: str) -> List[str]:
        """Extraire les thèmes depuis le titre du QCM"""
        # Simple extraction basée sur des mots-clés
        themes = []
        title_lower = title.lower()
        
        # Thèmes techniques
        if any(word in title_lower for word in ['optimisation', 'algorithme', 'programmation']):
            themes.append('Algorithmique')
        if any(word in title_lower for word in ['base de données', 'sql', 'bdd']):
            themes.append('Base de données')
        if any(word in title_lower for word in ['réseau', 'tcp', 'ip', 'internet']):
            themes.append('Réseaux')
        if any(word in title_lower for word in ['ia', 'intelligence artificielle', 'machine learning']):
            themes.append('Intelligence Artificielle')
        if any(word in title_lower for word in ['web', 'html', 'css', 'javascript']):
            themes.append('Développement Web')
        if any(word in title_lower for word in ['système', 'os', 'linux', 'windows']):
            themes.append('Systèmes')
        if any(word in title_lower for word in ['sécurité', 'cryptographie', 'authentification']):
            themes.append('Sécurité')
        if any(word in title_lower for word in ['gestion', 'projet', 'management']):
            themes.append('Gestion de projet')
        
        # Thème par défaut si aucun détecté
        if not themes:
            themes.append('Général')
        
        return themes
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Récupérer toutes les données pour le dashboard"""
        return progress_store.get_dashboard_data()
    
    def get_learning_analytics(self) -> Dict[str, Any]:
        """Récupérer des analytics avancées"""
        progress = progress_store.get_progress()
        sessions = progress_store.get_sessions()
        all_results = qcm_store.get_all_results()
        
        # Calculs avancés
        weekly_activity = self._calculate_weekly_activity(sessions)
        difficulty_analysis = self._analyze_difficulty(all_results)
        learning_trends = self._calculate_learning_trends(all_results)
        
        return {
            "weekly_activity": weekly_activity,
            "difficulty_analysis": difficulty_analysis,
            "learning_trends": learning_trends,
            "recommendations": self._generate_recommendations(progress, all_results)
        }
    
    def _calculate_weekly_activity(self, sessions: List) -> Dict[str, Any]:
        """Calculer l'activité hebdomadaire"""
        now = datetime.now()
        week_start = now - timedelta(days=7)
        
        weekly_sessions = [s for s in sessions if s.start_time >= week_start]
        
        daily_activity = {}
        for session in weekly_sessions:
            date_key = session.start_time.strftime("%Y-%m-%d")
            if date_key not in daily_activity:
                daily_activity[date_key] = {
                    "duration": 0,
                    "qcm_count": 0,
                    "activities": set()
                }
            
            daily_activity[date_key]["duration"] += session.duration or 0
            daily_activity[date_key]["qcm_count"] += len(session.qcm_results)
            daily_activity[date_key]["activities"].update(session.activities)
        
        # Convertir les sets en listes pour la sérialisation JSON
        for date_data in daily_activity.values():
            date_data["activities"] = list(date_data["activities"])
        
        return {
            "daily_breakdown": daily_activity,
            "total_sessions": len(weekly_sessions),
            "average_session_duration": sum(s.duration or 0 for s in weekly_sessions) / len(weekly_sessions) if weekly_sessions else 0
        }
    
    def _analyze_difficulty(self, results: List) -> Dict[str, Any]:
        """Analyser la difficulté par thème"""
        theme_stats = {}
        
        for result in results:
            for theme in result.themes:
                if theme not in theme_stats:
                    theme_stats[theme] = {
                        "total_questions": 0,
                        "correct_answers": 0,
                        "avg_time": 0,
                        "attempts": 0
                    }
                
                theme_stats[theme]["total_questions"] += result.total_questions
                theme_stats[theme]["correct_answers"] += result.score
                theme_stats[theme]["attempts"] += 1
                
                if result.completion_time:
                    theme_stats[theme]["avg_time"] += result.completion_time
        
        # Calculer les moyennes et difficultés
        for theme, stats in theme_stats.items():
            if stats["attempts"] > 0:
                stats["success_rate"] = (stats["correct_answers"] / stats["total_questions"]) * 100
                stats["avg_time"] = stats["avg_time"] / stats["attempts"]
                
                # Déterminer la difficulté (facile, moyen, difficile)
                if stats["success_rate"] >= 80:
                    stats["difficulty"] = "Facile"
                elif stats["success_rate"] >= 60:
                    stats["difficulty"] = "Moyen"
                else:
                    stats["difficulty"] = "Difficile"
        
        return theme_stats
    
    def _calculate_learning_trends(self, results: List) -> Dict[str, Any]:
        """Calculer les tendances d'apprentissage"""
        if not results:
            return {"trend": "stable", "improvement": 0}
        
        # Trier par date
        sorted_results = sorted(results, key=lambda x: x.completed_at)
        
        # Calculer la tendance sur les 5 derniers QCM
        recent_results = sorted_results[-5:]
        if len(recent_results) < 2:
            return {"trend": "insufficient_data", "improvement": 0}
        
        first_half = recent_results[:len(recent_results)//2]
        second_half = recent_results[len(recent_results)//2:]
        
        avg_first = sum(r.percentage for r in first_half) / len(first_half)
        avg_second = sum(r.percentage for r in second_half) / len(second_half)
        
        improvement = avg_second - avg_first
        
        if improvement > 5:
            trend = "improving"
        elif improvement < -5:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "improvement": round(improvement, 1),
            "recent_average": round(avg_second, 1)
        }
    
    def _generate_recommendations(self, progress, results: List) -> List[str]:
        """Générer des recommandations personnalisées"""
        recommendations = []
        
        # Recommandations basées sur les thèmes faibles
        if progress.weak_themes:
            recommendations.append(f"Concentrez-vous sur les thèmes suivants : {', '.join(progress.weak_themes[:3])}")
        
        # Recommandations basées sur le temps d'étude
        if progress.time_spent_learning < 7200:  # Moins de 2h
            recommendations.append("Essayez d'augmenter votre temps d'étude quotidien pour de meilleurs résultats")
        
        # Recommandations basées sur la régularité
        if progress.learning_streak < 3:
            recommendations.append("Maintenez une pratique régulière pour développer une habitude d'apprentissage")
        
        # Recommandations basées sur les performances récentes
        if results:
            recent_avg = sum(r.percentage for r in results[-3:]) / min(len(results), 3)
            if recent_avg < 70:
                recommendations.append("Revoyez les explications des questions ratées pour améliorer vos performances")
        
        return recommendations[:3]  # Maximum 3 recommandations
    
    def get_score_history(self) -> List[Dict[str, Any]]:
        """Récupérer l'historique des scores pour les graphiques"""
        try:
            # Récupérer les résultats des QCM
            results = qcm_store.get_all_results()
            
            if not results:
                return []
            
            # Grouper par date et calculer la moyenne quotidienne
            daily_scores = {}
            for result in results:
                # Utiliser completed_at ou completion_time, puis date actuelle par défaut
                date_obj = None
                if hasattr(result, 'completion_time') and result.completion_time:
                    date_obj = result.completion_time
                elif hasattr(result, 'completed_at') and result.completed_at:
                    date_obj = result.completed_at
                else:
                    date_obj = datetime.now()
                
                date_key = date_obj.strftime('%Y-%m-%d')
                
                if date_key not in daily_scores:
                    daily_scores[date_key] = []
                daily_scores[date_key].append(result.percentage)
            
            # Créer la liste finale avec moyennes
            score_history = []
            for date_str, scores in daily_scores.items():
                average_score = sum(scores) / len(scores)
                score_history.append({
                    'date': date_str,
                    'score': round(average_score, 1)
                })
            
            # Trier par date
            score_history.sort(key=lambda x: x['date'])            
            return score_history[-30:]  # Derniers 30 jours maximum
            
        except Exception as e:
            print(f"Erreur lors de la récupération de l'historique des scores : {e}")
            return []
    
    def get_recent_activities(self) -> List[Dict[str, Any]]:
        """Récupérer les activités récentes"""
        try:
            activities = []
            
            # Récupérer les QCM récents
            results = qcm_store.get_all_results()
            for result in results[-10:]:  # Derniers 10 QCM
                # Utiliser completion_time ou completed_at
                timestamp = getattr(result, 'completion_time', None) or getattr(result, 'completed_at', datetime.now())
                
                activities.append({
                    'type': 'qcm',
                    'description': f"QCM complété : {result.qcm_title or 'QCM'} - Score: {result.percentage}%",
                    'timestamp': timestamp
                })
              # Récupérer les activités depuis le progress_store s'il y en a
            try:
                progress = progress_store.get_progress()
                if hasattr(progress, 'recent_activities'):
                    for activity in progress.recent_activities[-5:]:  # Dernières 5 activités
                        activities.append({
                            'type': activity.get('type', 'other'),
                            'description': activity.get('description', 'Activité'),
                            'timestamp': activity.get('timestamp', datetime.now())
                        })
            except:
                pass
              # Trier par timestamp (plus récent en premier)
            activities.sort(key=lambda x: x['timestamp'], reverse=True)
            return activities[:10]  # Maximum 10 activités
            
        except Exception as e:
            print(f"Erreur lors de la récupération des activités : {e}")
            return []
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Récupérer les recommandations personnalisées"""
        try:
            recommendations = []
            
            # Récupérer les données de progression
            progress = progress_store.get_progress()
            results = qcm_store.get_all_results()
            # Génération de recommandations basée sur les performances
            if results:
                recent_avg = sum(r.percentage for r in results[-5:]) / min(len(results), 5)
                
                if recent_avg < 60:
                    recommendations.append({
                        'title': 'Améliorer vos performances',
                        'description': 'Vos scores récents sont en baisse. Prenez le temps de réviser les concepts de base.',
                        'icon': 'school'
                    })
                elif recent_avg > 80:
                    recommendations.append({
                        'title': 'Excellent travail !',
                        'description': 'Continuez sur cette lancée. Vous pourriez explorer des sujets plus avancés.',
                        'icon': 'star'
                    })
                else:
                    recommendations.append({
                        'title': 'Progression constante',
                        'description': 'Vous êtes sur la bonne voie. Un peu plus de pratique vous aidera à exceller.',
                        'icon': 'trending_up'
                    })
            
            # Recommandations basées sur les thèmes faibles
            if hasattr(progress, 'weak_themes') and progress.weak_themes:
                recommendations.append({
                    'title': 'Renforcer les thèmes faibles',                    'description': f"Concentrez-vous sur : {', '.join(progress.weak_themes[:2])}",
                    'icon': 'build'
                })
            # Recommandations de régularité
            if len(results) > 0:
                last_result = results[-1]
                # Utiliser completion_time ou completed_at
                last_completion = getattr(last_result, 'completion_time', None) or getattr(last_result, 'completed_at', None)
                if last_completion:
                    days_since_last = (datetime.now() - last_completion).days
                    if days_since_last > 3:
                        recommendations.append({
                            'title': 'Maintenir la régularité',
                            'description': 'Il y a quelques jours depuis votre dernière session. La régularité est clé pour progresser.',
                            'icon': 'schedule'
                        })
            
            # Si pas de recommandations spécifiques, ajouter une recommandation générale
            if not recommendations:
                recommendations.append({
                    'title': 'Commencer votre apprentissage',
                    'description': 'Commencez par télécharger un document et faire votre premier QCM pour obtenir des recommandations personnalisées.',
                    'icon': 'play_arrow'
                })
            
            return recommendations[:3]  # Maximum 3 recommandations
            
        except Exception as e:
            print(f"Erreur lors de la génération des recommandations : {e}")
            return [{
                'title': 'Continuez votre apprentissage !',
                'description': 'Utilisez l\'application davantage pour obtenir des recommandations personnalisées.',
                'icon': 'lightbulb'
            }]


# Instance globale du service stats
stats_service = StatsService()
