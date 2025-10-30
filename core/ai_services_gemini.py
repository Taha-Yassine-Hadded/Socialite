"""
Service de recommandation IA avec Google Gemini
Pour utilisateurs Premium et Business uniquement
"""

import os
import json
from django.conf import settings

# Configuration Gemini
try:
    import google.generativeai as genai
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
        print("✅ [GEMINI] API configurée avec succès")
    else:
        print("⚠️ [GEMINI] Clé API manquante dans .env")
except ImportError:
    print("⚠️ [GEMINI] Module google-generativeai non installé")
    genai = None


def generate_destination_recommendations(user_profile, wallet_balance=None, max_recommendations=5):
    """
    Génère des recommandations de destinations personnalisées avec Gemini
    
    Args:
        user_profile: Dict contenant le profil MongoDB de l'utilisateur
        wallet_balance: Solde disponible dans le wallet
        max_recommendations: Nombre maximum de recommandations
    
    Returns:
        Dict avec succès et liste de recommandations
    """
    if not genai or not GOOGLE_API_KEY:
        return {
            'success': False,
            'error': 'API Gemini non configurée',
            'recommendations': []
        }
    
    try:
        # Construire le prompt avec les données utilisateur
        interests = user_profile.get('interests', [])
        travel_types = user_profile.get('travel_type', [])
        languages = user_profile.get('languages', [])
        nationality = user_profile.get('nationality', '')
        travel_budget = user_profile.get('travel_budget', 'moyenne')
        
        prompt = f"""
Tu es un expert en voyage et tu dois recommander des destinations parfaites pour cet utilisateur.

PROFIL UTILISATEUR:
- Intérêts: {', '.join(interests) if interests else 'Divers'}
- Type de voyage préféré: {', '.join(travel_types) if travel_types else 'Flexible'}
- Langues parlées: {', '.join(languages) if languages else 'Non spécifié'}
- Nationalité: {nationality or 'Non spécifié'}
- Budget: {travel_budget}
- Solde disponible dans le wallet: {wallet_balance if wallet_balance else 'Non spécifié'} EUR

TÂCHE:
Recommande {max_recommendations} destinations de voyage parfaites pour cet utilisateur.

CONTRAINTES:
- Tenir compte du budget disponible
- Proposer des destinations variées
- Considérer les intérêts et le style de voyage
- Proposer des destinations accessibles linguistiquement si possible

FORMAT DE RÉPONSE (JSON strict):
{{
  "recommendations": [
    {{
      "destination": "Nom de la ville",
      "country": "Nom du pays",
      "estimated_budget": 1500,
      "currency": "EUR",
      "duration_days": 7,
      "best_season": "Printemps/Été/Automne/Hiver",
      "description": "Description courte (2-3 lignes)",
      "why_recommended": "Pourquoi cette destination correspond au profil",
      "activities": ["Activité 1", "Activité 2", "Activité 3"],
      "priority": 1-4,
      "tags": ["tag1", "tag2", "tag3"]
    }}
  ]
}}

Réponds UNIQUEMENT avec le JSON, sans texte supplémentaire.
"""
        
        print(f"🤖 [GEMINI] Génération de recommandations...")
        
        # Appeler l'API Gemini
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # Parser la réponse JSON
        response_text = response.text.strip()
        
        # Nettoyer la réponse si elle contient des balises markdown
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        elif response_text.startswith('```'):
            response_text = response_text.replace('```', '').strip()
        
        recommendations_data = json.loads(response_text)
        
        print(f"✅ [GEMINI] {len(recommendations_data.get('recommendations', []))} recommandations générées")
        
        return {
            'success': True,
            'recommendations': recommendations_data.get('recommendations', []),
            'total': len(recommendations_data.get('recommendations', []))
        }
    
    except json.JSONDecodeError as e:
        print(f"❌ [GEMINI] Erreur de parsing JSON : {e}")
        print(f"   Réponse brute : {response.text[:500]}")
        return {
            'success': False,
            'error': f'Erreur de parsing JSON: {str(e)}',
            'recommendations': [],
            'raw_response': response.text[:500]
        }
    
    except Exception as e:
        print(f"❌ [GEMINI] Erreur : {e}")
        return {
            'success': False,
            'error': str(e),
            'recommendations': []
        }


def generate_bucket_list_description(destination, country):
    """
    Génère une description attrayante pour un élément de bucket list
    
    Args:
        destination: Nom de la destination
        country: Nom du pays
    
    Returns:
        String avec la description générée
    """
    if not genai or not GOOGLE_API_KEY:
        return "Description non disponible (API Gemini non configurée)"
    
    try:
        prompt = f"""
Génère une description courte et inspirante (3-4 lignes) pour une destination de rêve.

Destination: {destination}
Pays: {country}

La description doit:
- Être engageante et donner envie de visiter
- Mentionner 2-3 points d'intérêt principaux
- Être concise et poétique
- Être en français

Réponds UNIQUEMENT avec la description, sans titre ni introduction.
"""
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        return response.text.strip()
    
    except Exception as e:
        print(f"❌ [GEMINI] Erreur description : {e}")
        return f"Découvrez {destination}, {country} - une destination qui vous fera rêver !"


def generate_trip_itinerary(destination, duration_days, interests):
    """
    Génère un itinéraire de voyage personnalisé
    
    Args:
        destination: Nom de la destination
        duration_days: Durée du séjour en jours
        interests: Liste des intérêts de l'utilisateur
    
    Returns:
        String avec l'itinéraire généré
    """
    if not genai or not GOOGLE_API_KEY:
        return "Itinéraire non disponible (API Gemini non configurée)"
    
    try:
        prompt = f"""
Crée un itinéraire de voyage détaillé pour:

Destination: {destination}
Durée: {duration_days} jours
Intérêts: {', '.join(interests) if interests else 'Découverte générale'}

Format:
Jour 1: [Activités]
Jour 2: [Activités]
...

L'itinéraire doit:
- Être réaliste et faisable
- Tenir compte des intérêts de l'utilisateur
- Inclure des temps de repos
- Mélanger attractions touristiques et expériences locales
- Être en français

Réponds de manière structurée et concise.
"""
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        return response.text.strip()
    
    except Exception as e:
        print(f"❌ [GEMINI] Erreur itinéraire : {e}")
        return "Itinéraire non disponible pour le moment."


def generate_travel_tips(destination, user_nationality):
    """
    Génère des conseils de voyage personnalisés
    
    Args:
        destination: Nom de la destination
        user_nationality: Nationalité de l'utilisateur
    
    Returns:
        String avec les conseils générés
    """
    if not genai or not GOOGLE_API_KEY:
        return "Conseils non disponibles (API Gemini non configurée)"
    
    try:
        prompt = f"""
Génère 5-7 conseils pratiques essentiels pour un voyageur de nationalité {user_nationality} 
qui visite {destination}.

Les conseils doivent couvrir:
- Formalités (visa, etc.)
- Sécurité
- Transport local
- Budget approximatif
- Meilleure période de visite
- Coutumes locales importantes

Format:
• Conseil 1
• Conseil 2
...

Sois concis et pratique. En français.
"""
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        return response.text.strip()
    
    except Exception as e:
        print(f"❌ [GEMINI] Erreur conseils : {e}")
        return "Conseils non disponibles pour le moment."


def analyze_spending_pattern(transactions):
    """
    Analyse les habitudes de dépenses et donne des recommandations
    
    Args:
        transactions: Liste des transactions du wallet
    
    Returns:
        Dict avec analyse et recommandations
    """
    if not genai or not GOOGLE_API_KEY or not transactions:
        return {
            'success': False,
            'analysis': 'Analyse non disponible',
            'recommendations': []
        }
    
    try:
        # Préparer les données de transaction
        transaction_summary = []
        for t in transactions[:20]:  # Limiter aux 20 dernières
            transaction_summary.append({
                'type': t.transaction_type,
                'amount': float(t.amount),
                'description': t.description,
                'date': t.created_at.strftime('%Y-%m-%d')
            })
        
        prompt = f"""
Analyse ces transactions de voyage et donne des recommandations financières:

TRANSACTIONS:
{json.dumps(transaction_summary, indent=2)}

TÂCHE:
1. Identifier les patterns de dépenses
2. Calculer le budget moyen par type de dépense
3. Donner 3-4 recommandations pour optimiser les dépenses

FORMAT (JSON):
{{
  "analysis": "Analyse courte des habitudes",
  "average_spending": 1234,
  "recommendations": [
    "Recommandation 1",
    "Recommandation 2"
  ]
}}

Réponds UNIQUEMENT avec le JSON.
"""
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # Parser la réponse
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        analysis_data = json.loads(response_text)
        
        return {
            'success': True,
            **analysis_data
        }
    
    except Exception as e:
        print(f"❌ [GEMINI] Erreur analyse : {e}")
        return {
            'success': False,
            'analysis': 'Analyse non disponible',
            'recommendations': []
        }