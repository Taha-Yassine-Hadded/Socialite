"""
Services IA pour Socialite
1. Transcription audio/vidéo avec Whisper (Speech-to-Text)
2. Classification d'images de voyage avec ResNet (Computer Vision)
"""
import whisper
import os
import sys
from django.conf import settings
import torch
from torchvision import transforms, models
from PIL import Image
import json

# Configuration du chemin FFmpeg pour Windows
# Ajouter les chemins communs où FFmpeg peut être installé
if sys.platform == 'win32':
    ffmpeg_paths = [
        r'C:\ProgramData\chocolatey\bin',
        r'C:\ffmpeg\bin',
        r'C:\Program Files\ffmpeg\bin',
        os.path.expanduser(r'~\AppData\Local\Microsoft\WinGet\Links'),
    ]
    for path in ffmpeg_paths:
        if os.path.exists(path) and path not in os.environ['PATH']:
            os.environ['PATH'] = path + os.pathsep + os.environ['PATH']
            print(f"✅ [FFmpeg] Ajouté au PATH : {path}")

# Charger le modèle Whisper une seule fois au démarrage
# Tailles disponibles : tiny, base, small, medium, large
# tiny = rapide mais moins précis (~39 MB, 1 GB VRAM)
# base = bon compromis (~74 MB, 1.5 GB VRAM) ← RECOMMANDÉ
# small = précis (~244 MB, 2.5 GB VRAM)
WHISPER_MODEL = None

def get_whisper_model():
    """
    Charge le modèle Whisper (une seule fois pour optimiser les performances).
    Le modèle est gardé en mémoire pour les transcriptions suivantes.
    
    Returns:
        whisper.model.Whisper: Modèle Whisper chargé
    """
    global WHISPER_MODEL
    if WHISPER_MODEL is None:
        print("🤖 [Whisper] Chargement du modèle 'base'... (première fois seulement)")
        WHISPER_MODEL = whisper.load_model("base")  # Changez en "tiny" pour plus rapide, "small" pour plus précis
        print("✅ [Whisper] Modèle chargé avec succès !")
    return WHISPER_MODEL


def transcribe_voice_note(audio_file):
    """
    Transcrit une note vocale en texte avec détection automatique de la langue.
    
    Args:
        audio_file (FileField): Fichier audio Django (post.voice_note)
    
    Returns:
        dict: {
            'text': str,          # Texte transcrit complet
            'language': str,      # Code langue détectée (ex: 'fr', 'ar', 'en')
            'language_name': str, # Nom de la langue (ex: 'French', 'Arabic', 'English')
            'success': bool,      # True si transcription réussie
            'error': str          # Message d'erreur si échec (optionnel)
        }
    
    Example:
        >>> result = transcribe_voice_note(post.voice_note)
        >>> if result['success']:
        >>>     print(f"Transcription ({result['language']}): {result['text']}")
    """
    try:
        # Vérifier que le fichier existe
        if not audio_file or not hasattr(audio_file, 'path'):
            return {
                'text': '',
                'language': None,
                'language_name': None,
                'success': False,
                'error': 'Fichier audio invalide ou manquant'
            }
        
        # Récupérer le chemin complet du fichier audio
        audio_path = audio_file.path
        
        if not os.path.exists(audio_path):
            return {
                'text': '',
                'language': None,
                'language_name': None,
                'success': False,
                'error': f'Fichier audio introuvable : {audio_path}'
            }
        
        # Charger le modèle Whisper
        model = get_whisper_model()
        
        # Transcription automatique avec détection de langue
        print(f"🎤 [Whisper] Transcription en cours : {os.path.basename(audio_file.name)}...")
        
        result = model.transcribe(
            audio_path,
            language=None,      # Auto-détection de la langue (ou spécifiez 'fr', 'ar', 'en')
            fp16=False,         # False pour compatibilité CPU (True si GPU NVIDIA disponible)
            verbose=False,      # Pas de logs verbeux
            task='transcribe'   # 'transcribe' ou 'translate' (vers anglais)
        )
        
        # Extraire les résultats
        transcription = result['text'].strip()
        detected_lang = result['language']
        
        # Mapper les codes de langue vers les noms complets
        language_names = {
            'fr': 'Français',
            'en': 'English',
            'ar': 'العربية',
            'es': 'Español',
            'de': 'Deutsch',
            'it': 'Italiano',
            'pt': 'Português',
            'ru': 'Русский',
            'zh': '中文',
            'ja': '日本語',
        }
        language_name = language_names.get(detected_lang, detected_lang.capitalize())
        
        print(f"✅ [Whisper] Transcription réussie !")
        print(f"   Langue détectée : {language_name} ({detected_lang})")
        print(f"   Texte ({len(transcription)} caractères) : {transcription[:100]}...")
        
        return {
            'text': transcription,
            'language': detected_lang,
            'language_name': language_name,
            'success': True
        }
    
    except Exception as e:
        print(f"❌ [Whisper] Erreur lors de la transcription : {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'text': '',
            'language': None,
            'language_name': None,
            'success': False,
            'error': str(e)
        }


def transcribe_with_timestamps(audio_file):
    """
    Transcription avec timestamps (pour sous-titres synchronisés).
    Utile pour afficher des sous-titres en temps réel pendant la lecture audio.
    
    Args:
        audio_file (FileField): Fichier audio Django
    
    Returns:
        dict: {
            'segments': list,  # Liste de segments [{start, end, text}, ...]
            'language': str,   # Langue détectée
            'success': bool
        }
    
    Example:
        >>> result = transcribe_with_timestamps(post.voice_note)
        >>> for segment in result['segments']:
        >>>     print(f"[{segment['start']:.2f}s - {segment['end']:.2f}s] {segment['text']}")
    """
    try:
        audio_path = audio_file.path
        model = get_whisper_model()
        
        print(f"🎤 [Whisper] Transcription avec timestamps : {os.path.basename(audio_file.name)}...")
        
        # Transcription avec segments temporels
        result = model.transcribe(
            audio_path,
            language=None,
            word_timestamps=True,  # Activer les timestamps par mot
            verbose=False
        )
        
        # Extraire les segments avec timestamps
        segments = []
        for segment in result.get('segments', []):
            segments.append({
                'start': round(segment['start'], 2),
                'end': round(segment['end'], 2),
                'text': segment['text'].strip()
            })
        
        print(f"✅ [Whisper] {len(segments)} segments extraits")
        
        return {
            'segments': segments,
            'language': result['language'],
            'success': True
        }
    
    except Exception as e:
        print(f"❌ [Whisper] Erreur : {str(e)}")
        return {
            'segments': [],
            'language': None,
            'success': False,
            'error': str(e)
        }


# ============================================
# CLASSIFICATION D'IMAGES DE VOYAGE
# ============================================

# Modèle de classification chargé une seule fois
TRAVEL_CLASSIFIER = None
TRAVEL_CLASSES = None

def get_travel_classifier():
    """
    Charge le modèle de classification d'images de voyage (une seule fois).
    Le modèle doit avoir été entraîné avec train_travel_classifier.py
    
    Returns:
        tuple: (model, class_names) ou (None, None) si modèle non trouvé
    """
    global TRAVEL_CLASSIFIER, TRAVEL_CLASSES
    
    if TRAVEL_CLASSIFIER is None:
        model_path = 'models/travel_classifier.pth'
        
        if not os.path.exists(model_path):
            print(f"⚠️  [Classifier] Modèle non trouvé : {model_path}")
            print("   Entraînez d'abord le modèle avec : python train_travel_classifier.py")
            return None, None
        
        try:
            print("🤖 [Classifier] Chargement du modèle de classification...")
            
            # Charger le modèle sauvegardé
            checkpoint = torch.load(model_path, map_location='cpu')
            
            # Recréer l'architecture
            num_classes = checkpoint['num_classes']
            model = models.resnet18(pretrained=False)
            model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
            
            # Charger les poids entraînés
            model.load_state_dict(checkpoint['model_state_dict'])
            model.eval()  # Mode évaluation
            
            TRAVEL_CLASSIFIER = model
            TRAVEL_CLASSES = checkpoint['class_names']
            
            accuracy = checkpoint.get('accuracy', 0) * 100
            print(f"✅ [Classifier] Modèle chargé ! Accuracy: {accuracy:.1f}%")
            print(f"   Classes : {', '.join(TRAVEL_CLASSES)}")
            
        except Exception as e:
            print(f"❌ [Classifier] Erreur de chargement : {e}")
            return None, None
    
    return TRAVEL_CLASSIFIER, TRAVEL_CLASSES


def classify_travel_image(image_file):
    """
    Classifie une image de voyage et retourne la catégorie prédite.
    
    Args:
        image_file (FileField): Image Django (post.image)
    
    Returns:
        dict: {
            'category': str,        # Catégorie prédite (ex: 'beach', 'mountain')
            'category_fr': str,     # Nom en français (ex: 'Plage', 'Montagne')
            'confidence': float,    # Score de confiance (0-1)
            'all_scores': dict,     # Tous les scores par catégorie
            'success': bool
        }
    
    Example:
        >>> result = classify_travel_image(post.image)
        >>> print(f"Catégorie : {result['category_fr']} ({result['confidence']*100:.1f}%)")
    """
    try:
        # Charger le modèle
        model, class_names = get_travel_classifier()
        
        if model is None:
            return {
                'category': None,
                'category_fr': None,
                'confidence': 0.0,
                'all_scores': {},
                'success': False,
                'error': 'Modèle non disponible'
            }
        
        # Transformations pour l'image
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        # Charger et transformer l'image
        image = Image.open(image_file.path).convert('RGB')
        image_tensor = transform(image).unsqueeze(0)  # Ajouter dimension batch
        
        # Prédiction
        with torch.no_grad():
            outputs = model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, predicted_idx = torch.max(probabilities, 0)
        
        # Récupérer le nom de la catégorie
        predicted_category = class_names[predicted_idx.item()]
        confidence_score = confidence.item()
        
        # Noms en français (alignés avec le dataset travel: buildings, forest, glacier, mountain, sea, street)
        category_names_fr = {
            'buildings': 'Bâtiments',
            'forest': 'Forêt',
            'glacier': 'Glacier',
            'mountain': 'Montagne',
            'sea': 'Mer',
            'street': 'Rue'
        }
        
        # Tous les scores
        all_scores = {
            class_names[i]: float(probabilities[i])
            for i in range(len(class_names))
        }
        
        print(f"✅ [Classifier] Image classifiée : {predicted_category} ({confidence_score*100:.1f}%)")
        
        return {
            'category': predicted_category,
            'category_fr': category_names_fr.get(predicted_category, predicted_category),
            'confidence': confidence_score,
            'all_scores': all_scores,
            'success': True
        }
    
    except Exception as e:
        print(f"❌ [Classifier] Erreur : {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'category': None,
            'category_fr': None,
            'confidence': 0.0,
            'all_scores': {},
            'success': False,
            'error': str(e)
        }


def get_image_tags(image_file):
    """
    Génère des tags automatiques pour une image (basé sur la classification).
    
    Args:
        image_file (FileField): Image Django
    
    Returns:
        list: Liste de tags suggérés
    
    Example:
        >>> tags = get_image_tags(post.image)
        >>> print(tags)  # ['plage', 'mer', 'voyage', 'été']
    """
    result = classify_travel_image(image_file)
    
    if not result['success']:
        return []
    
    # Tags basés sur la catégorie (alignés avec le dataset travel)
    category_tags = {
        'buildings': ['architecture', 'ville', 'urbain', 'batiment', 'cityscape'],
        'forest': ['nature', 'foret', 'arbres', 'verdure', 'wildlife'],
        'glacier': ['glacier', 'neige', 'froid', 'ice', 'montagne'],
        'mountain': ['montagne', 'randonnee', 'altitude', 'paysage', 'hiking'],
        'sea': ['mer', 'plage', 'ocean', 'sable', 'vacances'],
        'street': ['rue', 'urbain', 'voyage', 'city', 'streetphotography']
    }
    
    tags = category_tags.get(result['category'], [])
    
    # Ajouter des tags secondaires si confiance élevée
    if result['confidence'] > 0.7:
        tags.insert(0, result['category_fr'].lower())
    
    return tags[:5]  # Retourner top 5 tags


# ============================================
# FONCTIONS POUR L'ANALYSE AVANT PUBLICATION
# ============================================

def classify_travel_image_from_path(image_path):
    """
    Classifie une image de voyage à partir d'un chemin de fichier.
    Utilisé pour l'analyse AVANT publication (API temps réel).
    
    Args:
        image_path (str): Chemin complet vers l'image
    
    Returns:
        dict: {
            'category': str,        # Catégorie en anglais (ex: 'sea')
            'category_fr': str,     # Catégorie en français (ex: 'Mer')
            'confidence': float,    # Confiance 0-1
            'success': bool
        }
    """
    try:
        print(f"🖼️ [Classifier API] Analyse de l'image : {image_path}")
        
        model, class_names = get_travel_classifier()
        if model is None:
            return {'category': None, 'success': False, 'error': 'Modèle non disponible'}
        
        # Prétraitement de l'image
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        # Charger et transformer l'image
        image = Image.open(image_path).convert('RGB')
        image_tensor = transform(image).unsqueeze(0)
        
        # Prédiction
        with torch.no_grad():
            outputs = model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, predicted_idx = torch.max(probabilities, 0)
        
        predicted_category = class_names[predicted_idx.item()]
        confidence_score = confidence.item()
        
        # Mapping français
        category_names_fr = {
            'buildings': 'Bâtiments',
            'forest': 'Forêt',
            'glacier': 'Glacier',
            'mountain': 'Montagne',
            'sea': 'Mer',
            'street': 'Rue'
        }
        
        print(f"✅ [Classifier API] Catégorie : {predicted_category} ({confidence_score*100:.1f}%)")
        
        return {
            'category': predicted_category,
            'category_fr': category_names_fr.get(predicted_category, predicted_category),
            'confidence': confidence_score,
            'success': True
        }
    except Exception as e:
        print(f"❌ [Classifier API] Erreur : {str(e)}")
        import traceback
        traceback.print_exc()
        return {'category': None, 'success': False, 'error': str(e)}


def get_image_tags_from_classification(classification):
    """
    Génère des tags basés sur la classification d'image.
    Utilisé pour suggérer des hashtags AVANT publication.
    
    Args:
        classification (dict): Résultat de classify_travel_image_from_path()
    
    Returns:
        list: Liste de tags (sans le #)
    """
    if not classification.get('success'):
        return []
    
    category = classification.get('category', '')
    confidence = classification.get('confidence', 0)
    
    # Mapping catégories → tags
    tags_mapping = {
        'buildings': ['architecture', 'ville', 'urbain', 'batiment', 'cityscape'],
        'forest': ['nature', 'foret', 'arbres', 'verdure', 'wildlife'],
        'glacier': ['glacier', 'montagne', 'neige', 'froid', 'ice'],
        'mountain': ['montagne', 'nature', 'randonnee', 'altitude', 'hiking'],
        'sea': ['mer', 'plage', 'ocean', 'vacances', 'beach'],
        'street': ['rue', 'ville', 'urbain', 'voyage', 'streetphotography']
    }
    
    # Récupérer les tags correspondants
    tags = tags_mapping.get(category, ['voyage', 'travel'])
    
    # Si confiance élevée, retourner plus de tags
    if confidence > 0.8:
        return tags[:5]  # Top 5 tags
    elif confidence > 0.6:
        return tags[:3]  # Top 3 tags
    else:
        return tags[:2]  # Top 2 tags seulement
    
