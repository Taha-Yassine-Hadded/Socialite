"""
Service OCR (Optical Character Recognition) pour détecter la langue/pays à partir du texte dans l'image
Installation requise: pip install easyocr
"""
from PIL import Image
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

# Mapping langues → pays probables
LANGUAGE_TO_COUNTRIES = {
    'fr': ['France', 'Belgium', 'Switzerland', 'Canada', 'Morocco', 'Tunisia', 'Algeria'],
    'es': ['Spain', 'Mexico', 'Argentina', 'Colombia', 'Peru', 'Chile'],
    'de': ['Germany', 'Austria', 'Switzerland'],
    'it': ['Italy', 'Switzerland'],
    'pt': ['Portugal', 'Brazil'],
    'nl': ['Netherlands', 'Belgium'],
    'ar': ['Egypt', 'Morocco', 'United Arab Emirates', 'Saudi Arabia', 'Jordan', 'Tunisia'],
    'ja': ['Japan'],
    'ko': ['South Korea'],
    'zh_sim': ['China', 'Singapore'],
    'zh_tra': ['Taiwan', 'Hong Kong'],
    'th': ['Thailand'],
    'vi': ['Vietnam'],
    'ru': ['Russia', 'Ukraine', 'Belarus'],
    'el': ['Greece', 'Cyprus'],
    'tr': ['Turkey'],
    'pl': ['Poland'],
    'cs': ['Czech Republic'],
    'hu': ['Hungary'],
    'ro': ['Romania'],
    'bg': ['Bulgaria'],
    'hr': ['Croatia'],
    'sr': ['Serbia'],
    'uk': ['Ukraine'],
    'he': ['Israel'],
    'hi': ['India'],
    'bn': ['Bangladesh', 'India'],
    'ta': ['India', 'Sri Lanka'],
    'id': ['Indonesia'],
    'ms': ['Malaysia'],
    'sv': ['Sweden'],
    'no': ['Norway'],
    'da': ['Denmark'],
    'fi': ['Finland'],
    'is': ['Iceland'],
}

# Mots-clés typiques par pays pour affiner la détection
COUNTRY_KEYWORDS = {
    'France': ['rue', 'avenue', 'boulangerie', 'pharmacie', 'metro', 'sortie', 'entrée'],
    'Spain': ['calle', 'plaza', 'salida', 'entrada', 'restaurante'],
    'Italy': ['via', 'piazza', 'uscita', 'entrata', 'ristorante', 'gelato'],
    'Germany': ['straße', 'platz', 'ausgang', 'eingang', 'bahnhof'],
    'Japan': ['駅', '出口', '入口', '東京', '大阪'],
    'China': ['路', '街', '出口', '入口', '北京', '上海'],
    'United Kingdom': ['street', 'road', 'exit', 'way', 'underground', 'tube'],
    'United States': ['street', 'avenue', 'exit', 'way', 'downtown'],
}

try:
    import easyocr
    OCR_AVAILABLE = True
    # Initialiser le reader avec les langues les plus courantes
    # Note: Le premier appel télécharge les modèles (~100-500 MB selon les langues)
    _reader = None
    
    def _get_ocr_reader():
        """Lazy loading du reader OCR"""
        global _reader
        if _reader is None:
            # Langues les plus courantes pour le tourisme
            languages = ['en', 'fr', 'es', 'de', 'it', 'pt', 'ar', 'ja', 'ko', 'zh_sim', 'ru']
            _reader = easyocr.Reader(languages, gpu=False)  # CPU only
            logger.info(f"OCR Reader initialisé avec {len(languages)} langues")
        return _reader
        
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("EasyOCR n'est pas installé. Fonctionnalité OCR désactivée.")
    logger.warning("Pour activer: pip install easyocr")
    
    def _get_ocr_reader():
        raise ImportError("EasyOCR n'est pas installé")


def detect_text_language(image_bytes: bytes) -> dict:
    """
    Détecte la langue du texte dans l'image et retourne les pays probables
    
    Args:
        image_bytes: Bytes de l'image
        
    Returns:
        dict: {
            'countries': list[str],  # Pays probables
            'detected_languages': list[str],  # Langues détectées
            'confidence': float,  # Confiance globale (0-1)
            'extracted_text': str,  # Texte extrait
            'method': 'ocr'
        } ou None si échec ou pas de texte
    """
    if not OCR_AVAILABLE:
        logger.warning("OCR non disponible")
        return None
    
    try:
        reader = _get_ocr_reader()
        
        # Convertir bytes → PIL Image
        image = Image.open(BytesIO(image_bytes))
        
        # Effectuer l'OCR (retourne liste de (bbox, text, confidence))
        results = reader.readtext(image_bytes)
        
        if not results or len(results) == 0:
            logger.info("Aucun texte détecté dans l'image")
            return None
        
        # Extraire le texte et calculer confiance moyenne
        texts = []
        confidences = []
        
        for (bbox, text, conf) in results:
            if conf > 0.3:  # Filtrer les détections de faible confiance
                texts.append(text.lower())
                confidences.append(conf)
        
        if not texts:
            return None
        
        full_text = ' '.join(texts)
        avg_confidence = sum(confidences) / len(confidences)
        
        logger.info(f"Texte détecté: '{full_text[:100]}...' (confiance: {avg_confidence:.2f})")
        
        # Détecter les langues présentes
        detected_languages = reader.detect(image_bytes)
        
        # Mapper langues → pays
        probable_countries = set()
        for lang_code, _ in detected_languages:
            if lang_code in LANGUAGE_TO_COUNTRIES:
                probable_countries.update(LANGUAGE_TO_COUNTRIES[lang_code])
        
        # Affiner avec les mots-clés
        keyword_scores = {}
        for country, keywords in COUNTRY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in full_text)
            if score > 0:
                keyword_scores[country] = score
        
        # Si des mots-clés matchent, prioriser ces pays
        if keyword_scores:
            # Trier par score de mots-clés
            top_countries = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
            # Prendre les 3 premiers
            probable_countries = [country for country, _ in top_countries[:3]]
        else:
            probable_countries = list(probable_countries)[:5]
        
        if not probable_countries:
            return None
        
        return {
            'countries': probable_countries,
            'detected_languages': [lang for lang, _ in detected_languages],
            'confidence': avg_confidence,
            'extracted_text': full_text[:200],  # Limiter à 200 caractères
            'method': 'ocr'
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'OCR: {e}")
        return None


def detect_country_from_text(image_bytes: bytes) -> dict:
    """
    Version simplifiée qui retourne directement le pays le plus probable
    
    Returns:
        dict: {
            'country': str,
            'confidence': float,
            'method': 'ocr',
            'detected_text': str
        } ou None
    """
    result = detect_text_language(image_bytes)
    
    if not result or not result['countries']:
        return None
    
    return {
        'country': result['countries'][0],  # Premier pays le plus probable
        'confidence': result['confidence'],
        'method': 'ocr',
        'detected_text': result['extracted_text']
    }
