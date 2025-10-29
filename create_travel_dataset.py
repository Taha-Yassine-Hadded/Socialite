"""
Script pour créer automatiquement un dataset d'images de voyage
Télécharge des images depuis des sources publiques gratuites
"""
import os
import requests
from pathlib import Path
import time

# Configuration du dataset
DATASET_DIR = "ai_datasets/travel_images"
CATEGORIES = {
    'beach': 'Plage',
    'mountain': 'Montagne', 
    'city': 'Ville',
    'nature': 'Nature',
    'monument': 'Monument',
    'restaurant': 'Restaurant'
}

IMAGES_PER_CATEGORY = 300  # Nombre d'images par catégorie

# Sources d'images gratuites (Unsplash API - gratuit avec limite)
# Vous devrez créer une clé API gratuite sur https://unsplash.com/developers
UNSPLASH_ACCESS_KEY = "VOTRE_CLE_API_ICI"  # À remplacer

def create_dataset_structure():
    """
    Crée la structure de dossiers pour le dataset
    
    Structure créée :
    ai_datasets/
      └── travel_images/
          ├── train/
          │   ├── beach/
          │   ├── mountain/
          │   ├── city/
          │   ├── nature/
          │   ├── monument/
          │   └── restaurant/
          ├── validation/
          │   ├── beach/
          │   └── ...
          └── test/
              ├── beach/
              └── ...
    """
    print("📁 Création de la structure du dataset...")
    
    for split in ['train', 'validation', 'test']:
        for category in CATEGORIES.keys():
            path = Path(DATASET_DIR) / split / category
            path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ {split}/{category}")
    
    print("✅ Structure créée !\n")


def download_from_unsplash(category, query, num_images):
    """
    Télécharge des images depuis Unsplash (gratuit)
    
    Args:
        category: Nom de la catégorie
        query: Termes de recherche
        num_images: Nombre d'images à télécharger
    """
    if UNSPLASH_ACCESS_KEY == "VOTRE_CLE_API_ICI":
        print("❌ Vous devez configurer votre clé API Unsplash !")
        print("   1. Allez sur https://unsplash.com/developers")
        print("   2. Créez une application (gratuit)")
        print("   3. Copiez votre Access Key")
        print("   4. Remplacez VOTRE_CLE_API_ICI dans le script\n")
        return 0
    
    print(f"📥 Téléchargement de {num_images} images pour '{category}' (recherche: {query})...")
    
    base_url = "https://api.unsplash.com/search/photos"
    downloaded = 0
    
    # Répartition : 70% train, 20% validation, 10% test
    train_count = int(num_images * 0.7)
    val_count = int(num_images * 0.2)
    test_count = num_images - train_count - val_count
    
    splits = [
        ('train', train_count),
        ('validation', val_count),
        ('test', test_count)
    ]
    
    page = 1
    for split, count in splits:
        for i in range(count):
            try:
                # Requête API Unsplash
                params = {
                    'query': query,
                    'page': page,
                    'per_page': 30,
                    'client_id': UNSPLASH_ACCESS_KEY
                }
                
                response = requests.get(base_url, params=params)
                if response.status_code != 200:
                    print(f"   ❌ Erreur API: {response.status_code}")
                    break
                
                data = response.json()
                if not data['results']:
                    print(f"   ⚠️  Plus d'images disponibles pour '{query}'")
                    break
                
                # Télécharger l'image
                image_index = i % len(data['results'])
                image_url = data['results'][image_index]['urls']['regular']
                image_id = data['results'][image_index]['id']
                
                # Sauvegarder l'image
                img_path = Path(DATASET_DIR) / split / category / f"{category}_{image_id}.jpg"
                img_data = requests.get(image_url).content
                
                with open(img_path, 'wb') as f:
                    f.write(img_data)
                
                downloaded += 1
                if downloaded % 10 == 0:
                    print(f"   📥 {downloaded}/{num_images} téléchargées...")
                
                # Pause pour respecter les limites de l'API
                time.sleep(0.5)
                
                if (i + 1) % 30 == 0:
                    page += 1
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                continue
    
    print(f"   ✅ {downloaded} images téléchargées pour '{category}'\n")
    return downloaded


def download_dataset():
    """
    Télécharge le dataset complet pour toutes les catégories
    """
    # Termes de recherche optimisés pour chaque catégorie
    search_queries = {
        'beach': 'beach sunset ocean',
        'mountain': 'mountain hiking landscape',
        'city': 'city urban architecture',
        'nature': 'nature forest lake',
        'monument': 'monument landmark historical',
        'restaurant': 'restaurant food dining'
    }
    
    total_downloaded = 0
    
    for category, query in search_queries.items():
        print(f"\n{'='*60}")
        print(f"Catégorie : {CATEGORIES[category]} ({category})")
        print(f"{'='*60}")
        
        downloaded = download_from_unsplash(category, query, IMAGES_PER_CATEGORY)
        total_downloaded += downloaded
    
    print(f"\n{'='*60}")
    print(f"✅ TÉLÉCHARGEMENT TERMINÉ !")
    print(f"   Total : {total_downloaded} images")
    print(f"{'='*60}\n")


def generate_dataset_info():
    """
    Génère un fichier d'informations sur le dataset
    """
    info = f"""
╔══════════════════════════════════════════════════════════╗
║  DATASET : CLASSIFICATION D'IMAGES DE VOYAGE            ║
╚══════════════════════════════════════════════════════════╝

📊 INFORMATIONS GÉNÉRALES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Nom du dataset      : Travel Images Classification Dataset
Créé le             : {time.strftime('%Y-%m-%d %H:%M:%S')}
Objectif            : Classifier automatiquement les photos de voyage
Nombre de classes   : {len(CATEGORIES)}
Images par classe   : ~{IMAGES_PER_CATEGORY}
Total images        : ~{IMAGES_PER_CATEGORY * len(CATEGORIES)}

📁 CLASSES (CATÉGORIES)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
    for idx, (code, name) in enumerate(CATEGORIES.items(), 1):
        info += f"{idx}. {name.upper()} ({code})\n"
    
    info += f"""
🔄 RÉPARTITION DES DONNÉES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Train       : 70% (~{int(IMAGES_PER_CATEGORY * 0.7)} images/classe)
Validation  : 20% (~{int(IMAGES_PER_CATEGORY * 0.2)} images/classe)
Test        : 10% (~{int(IMAGES_PER_CATEGORY * 0.1)} images/classe)

📌 UTILISATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Entraînement : Utilisez les données de 'train/'
2. Validation   : Utilisez les données de 'validation/' pour ajuster les hyperparamètres
3. Test         : Utilisez les données de 'test/' pour évaluer la précision finale

🔧 PROCHAINES ÉTAPES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Exécuter : python train_travel_classifier.py
2. Le modèle sera sauvegardé dans : models/travel_classifier.pth
3. Intégrer dans Django avec : core/ai_services.py

"""
    
    # Sauvegarder le fichier
    with open(Path(DATASET_DIR) / 'DATASET_INFO.txt', 'w', encoding='utf-8') as f:
        f.write(info)
    
    print(info)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 CRÉATION DU DATASET D'IMAGES DE VOYAGE")
    print("="*60 + "\n")
    
    # Étape 1 : Créer la structure
    create_dataset_structure()
    
    # Étape 2 : Télécharger les images
    print("📥 TÉLÉCHARGEMENT DES IMAGES")
    print("━" * 60)
    print("⚠️  IMPORTANT : Configurez votre clé API Unsplash d'abord !")
    print("   (Gratuit, limite : 50 requêtes/heure)")
    print("━" * 60 + "\n")
    
    choice = input("Voulez-vous télécharger maintenant ? (oui/non) : ").strip().lower()
    
    if choice in ['oui', 'o', 'yes', 'y']:
        download_dataset()
    else:
        print("\n⏭️  Téléchargement annulé.")
        print("   Vous pouvez ajouter vos propres images manuellement dans les dossiers.")
    
    # Étape 3 : Générer les infos
    generate_dataset_info()
    
    print("\n✅ Dataset prêt pour l'entraînement !")
    print("   Prochaine étape : python train_travel_classifier.py\n")


