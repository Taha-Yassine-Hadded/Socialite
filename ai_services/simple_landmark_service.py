"""Service simplifié de détection de landmarks pour démonstration"""
import logging
import random
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

# Mapping landmarks → pays (version simplifiée)
LANDMARKS_BY_COUNTRY = {
    "France": [
        "Eiffel Tower", "Arc de Triomphe", "Louvre Museum", "Notre-Dame Cathedral",
        "Sacré-Cœur", "Versailles Palace", "Mont Saint-Michel"
    ],
    "Italy": [
        "Colosseum", "Leaning Tower of Pisa", "Venice canals", "Trevi Fountain",
        "Vatican", "Duomo di Milano", "Ponte Vecchio"
    ],
    "Spain": [
        "Sagrada Familia", "Alhambra", "Park Güell", "Plaza Mayor Madrid",
        "Mezquita Cordoba", "Seville Cathedral", "Giralda tower"
    ],
    "Egypt": [
        "Pyramids of Giza", "Sphinx", "Abu Simbel", "Karnak Temple",
        "Valley of the Kings", "Luxor Temple"
    ],
}

def detect_landmark_country(image_bytes: bytes) -> dict:
    """
    Version simplifiée de détection de landmarks qui utilise CLIP si disponible
    Sinon, retourne un résultat par défaut pour la France
    
    Returns:
        dict: {
            'country': str,
            'landmark': str,
            'confidence': float,
            'method': 'landmark'
        } ou None si aucun landmark détecté
    """
    try:
        # Essayer d'abord d'utiliser le vrai service de détection avec CLIP
        try:
            from ai_services.landmark_service import detect_landmark_country as detect_with_clip
            result = detect_with_clip(image_bytes)
            if result:
                logger.info(f"Landmark détecté avec CLIP: {result['landmark']} ({result['country']})")
                return result
        except Exception as e:
            logger.warning(f"Impossible d'utiliser CLIP, fallback vers détection simple: {e}")
        
        # Fallback: Analyse simplifiée basée sur l'image
        buffer = image_bytes if hasattr(image_bytes, "read") else BytesIO(image_bytes)
        image = Image.open(buffer).convert("RGB")
        width, height = image.size
        
        # Prendre plusieurs échantillons pour une meilleure détection
        sample_points = [
            (width // 4, height // 4),
            (width // 2, height // 2),
            (3 * width // 4, 3 * height // 4),
            (width // 4, 3 * height // 4),
            (3 * width // 4, height // 4),
        ]
        
        colors = []
        for x, y in sample_points:
            try:
                colors.append(image.getpixel((min(x, width-1), min(y, height-1))))
            except:
                pass
        
        if not colors:
            colors = [image.getpixel((width // 2, height // 2))]
        
        # Calculer la couleur moyenne
        avg_r = sum(c[0] for c in colors) / len(colors)
        avg_g = sum(c[1] for c in colors) / len(colors)
        avg_b = sum(c[2] for c in colors) / len(colors)
        
        # Logique simplifiée de détection
        # Heuristique pour la Tour Eiffel : image plutôt verticale + ciel bleu dominant
        aspect_ratio = height / max(1, width)
        if (avg_b > avg_r + 20 and avg_b > avg_g + 20) and aspect_ratio > 1.2:
            country = "France"
            landmark = "Eiffel Tower"
            confidence = 0.78
        elif avg_r > 200 and avg_g < 100 and avg_b < 100:  # Rouge dominant
            country = "Spain"
            landmark = random.choice(LANDMARKS_BY_COUNTRY["Spain"])
            confidence = 0.65
        elif avg_g > 150:  # Vert dominant
            country = "Italy"
            landmark = random.choice(LANDMARKS_BY_COUNTRY["Italy"])
            confidence = 0.65
        elif avg_r > 180 and avg_g > 180 and avg_b < 100:  # Jaune/Orange dominant
            country = "Egypt"
            landmark = "Pyramids of Giza"
            confidence = 0.70
        else:
            # Incertain → ne rien renvoyer pour éviter des faux positifs systématiques
            return None
        
        logger.info(f"Landmark détecté (simple): {landmark} ({country}) - confiance: {confidence:.2f}")
        
        return {
            'country': country,
            'landmark': landmark,
            'confidence': float(confidence),
            'method': 'landmark'
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la détection de landmark: {e}")
        # Échec silencieux pour laisser les autres méthodes (EXIF/CLIP) décider
        return None