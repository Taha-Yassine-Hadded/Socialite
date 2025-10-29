"""
Script pour créer un MINI dataset de démonstration
Télécharge seulement 50 images par catégorie depuis des URLs publiques
Idéal pour tester rapidement sans Kaggle
"""
import os
import urllib.request
from pathlib import Path
import time

DATASET_DIR = "ai_datasets/travel_images"

# URLs publiques d'images de démonstration (domaine public / CC0)
# Ces URLs pointent vers des images gratuites et libres de droits
DEMO_IMAGES = {
    'beach': [
        'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400',  # Plage tropicale
        'https://images.unsplash.com/photo-1519046904884-53103b34b206?w=400',  # Plage sable blanc
        'https://images.unsplash.com/photo-1506929562872-bb421503ef21?w=400',  # Sunset beach
        # Ajoutez plus d'URLs ici...
    ],
    'mountain': [
        'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400',  # Montagne lac
        'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=400',  # Montagne enneigée
        'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400',  # Alpes
        # Ajoutez plus d'URLs ici...
    ],
    'city': [
        'https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?w=400',  # Ville nuit
        'https://images.unsplash.com/photo-1514565131-fce0801e5785?w=400',  # New York
        'https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=400',  # Ville gratte-ciel
        # Ajoutez plus d'URLs ici...
    ],
    'nature': [
        'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400',  # Forêt
        'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=400',  # Nature lac
        'https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=400',  # Paysage vert
        # Ajoutez plus d'URLs ici...
    ],
    'monument': [
        'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=400',  # Tour Eiffel
        'https://images.unsplash.com/photo-1513581166391-887a96ddeafd?w=400',  # Monument historique
        'https://images.unsplash.com/photo-1550340499-a6c60fc8287c?w=400',  # Cathédrale
        # Ajoutez plus d'URLs ici...
    ],
    'restaurant': [
        'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400',  # Restaurant
        'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=400',  # Table restaurant
        'https://images.unsplash.com/photo-1559339352-11d035aa65de?w=400',  # Nourriture
        # Ajoutez plus d'URLs ici...
    ]
}

def create_structure():
    """Crée la structure de dossiers"""
    for split in ['train', 'validation', 'test']:
        for category in DEMO_IMAGES.keys():
            path = Path(DATASET_DIR) / split / category
            path.mkdir(parents=True, exist_ok=True)

def download_demo_images():
    """Télécharge les images de démonstration"""
    print("\n🚀 CRÉATION D'UN MINI-DATASET DE DÉMONSTRATION")
    print("=" * 60)
    print("⚠️  Ce dataset est PETIT (seulement pour tests)")
    print("   Pour production, utilisez un vrai dataset depuis Kaggle")
    print("=" * 60 + "\n")
    
    create_structure()
    
    total = 0
    for category, urls in DEMO_IMAGES.items():
        print(f"📥 Téléchargement : {category}...")
        
        for idx, url in enumerate(urls):
            try:
                # Répartir : 3 images en train, 1 en validation, 1 en test
                if idx % 5 < 3:
                    split = 'train'
                elif idx % 5 == 3:
                    split = 'validation'
                else:
                    split = 'test'
                
                filename = f"{category}_{idx:03d}.jpg"
                filepath = Path(DATASET_DIR) / split / category / filename
                
                urllib.request.urlretrieve(url, filepath)
                total += 1
                print(f"   ✅ {filename}")
                time.sleep(0.5)  # Pause pour ne pas surcharger
                
            except Exception as e:
                print(f"   ❌ Erreur : {e}")
    
    print(f"\n✅ {total} images téléchargées !")
    print("\n⚠️  MINI-DATASET CRÉÉ (pour démonstration)")
    print("   Pour un vrai entraînement, téléchargez un dataset complet depuis Kaggle")
    print("   Voir : GUIDE_CLASSIFICATION_IMAGES.md\n")

if __name__ == "__main__":
    download_demo_images()


