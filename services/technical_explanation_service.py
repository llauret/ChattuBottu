"""
Service pour les explications techniques détaillées et les démonstrations interactives
"""
from typing import Dict, List, Any, Optional
from services.llm_service import llm_service
from models import document_store


class TechnicalExplanationService:
    """Service pour générer des explications techniques détaillées avec exemples"""
    
    def __init__(self):
        self.algorithm_templates = {
            'sorting': self._get_sorting_template(),
            'search': self._get_search_template(),
            'recursion': self._get_recursion_template(),
            'dynamic_programming': self._get_dp_template(),
            'data_structures': self._get_ds_template()
        }
    
    def generate_step_by_step_explanation(self, user_query: str, context: str = "") -> Dict[str, Any]:
        """Générer une explication détaillée étape par étape"""
        
        # Détecter le type d'explication nécessaire
        explanation_type = self._detect_explanation_type(user_query)
        
        # Générer l'explication avec le template approprié
        if explanation_type in self.algorithm_templates:
            return self._generate_algorithm_explanation(user_query, context, explanation_type)
        else:
            return self._generate_general_technical_explanation(user_query, context)
    
    def _detect_explanation_type(self, query: str) -> str:
        """Détecter le type d'explication technique nécessaire"""
        query_lower = query.lower()
        
        sorting_keywords = ['tri', 'trier', 'sort', 'bubble', 'quick', 'merge', 'heap']
        search_keywords = ['recherche', 'search', 'binary', 'linear', 'find', 'chercher']
        recursion_keywords = ['récursion', 'recursive', 'récursif', 'factorielle', 'fibonacci']
        dp_keywords = ['programmation dynamique', 'dynamic programming', 'memoization']
        ds_keywords = ['liste', 'pile', 'file', 'arbre', 'graph', 'stack', 'queue', 'tree']
        
        if any(keyword in query_lower for keyword in sorting_keywords):
            return 'sorting'
        elif any(keyword in query_lower for keyword in search_keywords):
            return 'search'
        elif any(keyword in query_lower for keyword in recursion_keywords):
            return 'recursion'
        elif any(keyword in query_lower for keyword in dp_keywords):
            return 'dynamic_programming'
        elif any(keyword in query_lower for keyword in ds_keywords):
            return 'data_structures'
        
        return 'general'
    
    def _generate_algorithm_explanation(self, query: str, context: str, algo_type: str) -> Dict[str, Any]:
        """Générer une explication d'algorithme avec template spécialisé"""
        template = self.algorithm_templates.get(algo_type, self.algorithm_templates['sorting'])
        
        prompt = f"""Tu es un expert en algorithmes et programmation. Explique {query} en suivant cette structure précise :

{template}

RÈGLES IMPORTANTES :
- Utilise des exemples concrets et des cas d'usage réels
- Fournis du code Python simple et bien commenté
- Marque les blocs de code exécutables avec ```python-executable
- Inclus des exemples numériques step-by-step
- Explique la complexité temporelle et spatiale
- Donne des conseils d'optimisation

Contexte disponible : {context}

Réponds en français de manière claire et pédagogique."""

        try:
            response = llm_service.get_completion(prompt)
            return {
                "success": True,
                "explanation": response,
                "type": "algorithm",
                "algorithm_type": algo_type
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_general_technical_explanation(self, query: str, context: str) -> Dict[str, Any]:
        """Générer une explication technique générale"""
        prompt = f"""Tu es un assistant pédagogique expert. Explique {query} de manière détaillée et structurée.

STRUCTURE REQUISE :
1. **Concept principal** : Définition claire et concise
2. **Principes fondamentaux** : Les bases à comprendre
3. **Exemple concret** : Cas d'usage pratique avec code si pertinent
4. **Étapes détaillées** : Décomposition du processus
5. **Code exécutable** : Exemples Python commentés (utilise ```python-executable)
6. **Applications pratiques** : Où et comment l'utiliser
7. **Pièges à éviter** : Erreurs communes et solutions

Contexte disponible : {context}

Réponds en français de manière claire et pédagogique."""

        try:
            response = llm_service.get_completion(prompt)
            return {
                "success": True,
                "explanation": response,
                "type": "general_technical"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_sorting_template(self) -> str:
        return """
1. **Concept et principe** : Qu'est-ce que cet algorithme de tri ?
2. **Fonctionnement étape par étape** : Comment ça marche ?
3. **Exemple concret** : Tri d'un tableau [64, 34, 25, 12, 22, 11, 90]
4. **Code Python exécutable** : Implémentation simple
5. **Analyse de complexité** : Temps et espace
6. **Avantages et inconvénients** : Quand l'utiliser ?
7. **Variantes et optimisations** : Améliorations possibles
"""
    
    def _get_search_template(self) -> str:
        return """
1. **Principe de recherche** : Comment fonctionne l'algorithme ?
2. **Prérequis** : Conditions nécessaires (tri, structure, etc.)
3. **Démonstration** : Recherche de la valeur 22 dans [11, 22, 34, 45, 67, 89]
4. **Code Python exécutable** : Implémentation avec exemples
5. **Analyse de performance** : Complexité temporelle et spatiale
6. **Comparaison** : Avec d'autres méthodes de recherche
7. **Applications** : Cas d'usage concrets
"""
    
    def _get_recursion_template(self) -> str:
        return """
1. **Concept de récursion** : Définition et principe
2. **Cas de base et récurrence** : Structure d'une fonction récursive
3. **Exemple classique** : Factorielle, Fibonacci, ou autre
4. **Trace d'exécution** : Suivi pas à pas des appels
5. **Code Python exécutable** : Implémentation avec visualisation
6. **Pile d'appels** : Comment ça fonctionne en mémoire
7. **Récursion vs itération** : Avantages et inconvénients
"""
    
    def _get_dp_template(self) -> str:
        return """
1. **Programmation dynamique** : Principe et motivation
2. **Problème et sous-problèmes** : Décomposition
3. **Mémorisation** : Éviter les calculs redondants
4. **Exemple concret** : Problème classique step-by-step
5. **Code Python exécutable** : Implémentation avec cache
6. **Bottom-up vs Top-down** : Deux approches
7. **Applications** : Problèmes résolus par DP
"""
    
    def _get_ds_template(self) -> str:
        return """
1. **Structure de données** : Définition et utilité
2. **Opérations principales** : Insertion, suppression, recherche
3. **Implémentation** : Comment construire cette structure
4. **Code Python exécutable** : Classe avec méthodes
5. **Complexité des opérations** : Analyse temporelle
6. **Cas d'usage** : Quand utiliser cette structure
7. **Alternatives** : Comparaison avec d'autres structures
"""
    
    def generate_interactive_demo(self, algorithm_name: str) -> Dict[str, Any]:
        """Générer une démonstration interactive pour un algorithme"""
        
        demos = {
            'bubble_sort': self._create_bubble_sort_demo(),
            'binary_search': self._create_binary_search_demo(),
            'factorial': self._create_factorial_demo(),
            'fibonacci': self._create_fibonacci_demo()
        }
        
        return demos.get(algorithm_name.lower(), self._create_generic_demo())
    
    def _create_bubble_sort_demo(self) -> Dict[str, Any]:
        return {
            "title": "Tri à bulles interactif",
            "description": "Entrez des nombres séparés par des virgules",
            "input_type": "text",
            "placeholder": "Ex: 64, 34, 25, 12, 22",
            "code_template": """
def bubble_sort(arr):
    n = len(arr)
    steps = []
    
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                steps.append(f"Échange: {arr}")
    
    return arr, steps

# Votre tableau : {input_array}
result, steps = bubble_sort({input_array})
print(f"Tableau trié : {result}")
print("Étapes :")
for step in steps:
    print(step)
"""
        }
    
    def _create_binary_search_demo(self) -> Dict[str, Any]:
        return {
            "title": "Recherche binaire interactive",
            "description": "Rechercher une valeur dans un tableau trié",
            "input_type": "number",
            "placeholder": "Valeur à rechercher",
            "code_template": """
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    steps = []
    
    while left <= right:
        mid = (left + right) // 2
        steps.append(f"Milieu: index {mid}, valeur {arr[mid]}")
        
        if arr[mid] == target:
            return mid, steps
        elif arr[mid] < target:
            left = mid + 1
            steps.append(f"Chercher à droite (indices {left}-{right})")
        else:
            right = mid - 1
            steps.append(f"Chercher à gauche (indices {left}-{right})")
    
    return -1, steps

# Tableau trié : [11, 22, 34, 45, 67, 89]
# Recherche de : {target}
arr = [11, 22, 34, 45, 67, 89]
result, steps = binary_search(arr, {target})
print(f"Position de {target}: {result}")
print("Étapes :")
for step in steps:
    print(step)
"""
        }
    
    def _create_factorial_demo(self) -> Dict[str, Any]:
        return {
            "title": "Factorielle récursive",
            "description": "Calculer la factorielle d'un nombre",
            "input_type": "number",
            "placeholder": "Nombre (max 10)",
            "code_template": """
def factorial(n, depth=0):
    indent = "  " * depth
    print(f"{indent}factorial({n}) appelé")
    
    if n <= 1:
        print(f"{indent}Cas de base: factorial({n}) = 1")
        return 1
    
    result = n * factorial(n - 1, depth + 1)
    print(f"{indent}factorial({n}) = {n} × factorial({n-1}) = {result}")
    return result

# Calcul de {n}!
result = factorial({n})
print(f"\\nRésultat final: {n}! = {result}")
"""
        }
    
    def _create_fibonacci_demo(self) -> Dict[str, Any]:
        return {
            "title": "Suite de Fibonacci",
            "description": "Calculer le n-ième terme de Fibonacci",
            "input_type": "number",
            "placeholder": "Position (max 15)",
            "code_template": """
def fibonacci(n, memo={}):
    if n in memo:
        print(f"Valeur mémorisée: fib({n}) = {memo[n]}")
        return memo[n]
    
    if n <= 1:
        print(f"Cas de base: fib({n}) = {n}")
        return n
    
    print(f"Calcul de fib({n}) = fib({n-1}) + fib({n-2})")
    result = fibonacci(n - 1, memo) + fibonacci(n - 2, memo)
    memo[n] = result
    print(f"Mémorisation: fib({n}) = {result}")
    return result

# Calcul de fibonacci({n})
result = fibonacci({n})
print(f"\\nRésultat: Le {n}ème terme de Fibonacci est {result}")
"""
        }
    
    def _create_generic_demo(self) -> Dict[str, Any]:
        return {
            "title": "Démonstration générique",
            "description": "Entrez une valeur pour tester",
            "input_type": "text",
            "placeholder": "Votre valeur",
            "code_template": """
# Votre valeur : {input_value}
print(f"Traitement de : {input_value}")
"""
        }


# Instance globale
technical_explanation_service = TechnicalExplanationService()
