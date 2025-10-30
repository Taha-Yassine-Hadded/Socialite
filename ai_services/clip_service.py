from transformers import CLIPProcessor, CLIPModel
from PIL import Image
from io import BytesIO
import torch
import time
from typing import List, Dict, Optional
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration du modèle
MODEL_NAME = "openai/clip-vit-base-patch32"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Variables globales pour le chargement lazy
_model = None
_processor = None

def _get_model_and_processor():
    """Charge le modèle et le processeur CLIP (lazy loading)"""
    global _model, _processor
    if _model is None or _processor is None:
        try:
            _model = CLIPModel.from_pretrained(MODEL_NAME).to(DEVICE)
            _processor = CLIPProcessor.from_pretrained(MODEL_NAME)
            logger.info(f"Modèle CLIP chargé sur {DEVICE}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle CLIP: {e}")
            raise
    return _model, _processor

class ClipService:
    """
    Service pour la classification d'images avec CLIP
    """
    
    @staticmethod
    def zero_shot_countries(
        image_bytes: bytes, 
        candidate_countries: List[str],
        continent: Optional[str] = None
    ) -> List[Dict[str, float]]:
        """
        Classe l'image parmi une liste de pays candidats en utilisant CLIP
        
        Args:
            image_bytes: Bytes de l'image
            candidate_countries: Liste des noms de pays à considérer
            continent: Continent pour filtrer les pays (optionnel)
            
        Returns:
            Liste triée des pays avec leurs scores de confiance
        """
        start_time = time.time()
        
        try:
            # Charger le modèle
            model, processor = _get_model_and_processor()
            
            # Préparation de l'image
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
            
            # Création des prompts pour chaque pays avec contexte enrichi
            prompts = [f"a travel photo from {country}" for country in candidate_countries]
            
            # Traiter chaque pays un par un pour éviter les problèmes de padding
            scores = []
            with torch.no_grad():
                # Encoder l'image une seule fois
                image_inputs = processor(images=[image], return_tensors="pt")
                image_inputs = {k: v.to(DEVICE) for k, v in image_inputs.items()}
                image_features = model.get_image_features(**image_inputs)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                
                # Encoder chaque texte séparément
                for prompt in prompts:
                    text_inputs = processor(text=prompt, return_tensors="pt", padding=True)
                    text_inputs = {k: v.to(DEVICE) for k, v in text_inputs.items()}
                    text_features = model.get_text_features(**text_inputs)
                    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                    
                    # Calculer la similarité
                    similarity = (image_features @ text_features.T).item()
                    scores.append(similarity)
            
            # Convertir les scores en probabilités avec softmax
            scores_tensor = torch.tensor(scores)
            probs = scores_tensor.softmax(dim=0)
            
            # Association des scores aux pays
            results = []
            for country, score in zip(candidate_countries, probs):
                results.append({
                    'country': country,
                    'score': round(score.item(), 4)
                })
            
            # Tri par score décroissant
            results.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f"Inférence CLIP terminée en {time.time() - start_time:.2f}s")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la classification avec CLIP: {e}")
            return []
    
    @staticmethod
    def predict_continent(
        image_bytes: bytes,
        continents: List[str]
    ) -> Optional[str]:
        """
        Prédit le continent d'une image
        
        Args:
            image_bytes: Bytes de l'image
            continents: Liste des continents à considérer
            
        Returns:
            Le continent prédit ou None en cas d'erreur
        """
        try:
            results = ClipService.zero_shot_countries(image_bytes, continents)
            return results[0]['country'] if results else None
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction du continent: {e}")
            return None
