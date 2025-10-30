"""
Script pour télécharger des datasets publics d'images de voyage
Alternative gratuite sans API (utilise des datasets Kaggle publics)
"""
import os
import urllib.request
import zipfile
from pathlib import Path
import shutil

DATASET_DIR = "ai_datasets/travel_images"

print("""
╔══════════════════════════════════════════════════════════════╗
║  TÉLÉCHARGEMENT DE DATASETS PUBLICS D'IMAGES DE VOYAGE      ║
╚══════════════════════════════════════════════════════════════╝

🎓 MÉTHODE ACADÉMIQUE : Datasets publics gratuits
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 OPTION 1 : Téléchargement manuel depuis Kaggle (RECOMMANDÉ)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Dataset suggéré : "Travel Destination Classification"
Lien : https://www.kaggle.com/datasets/nih1l/travel-destination-classification

📥 ÉTAPES :
1. Créez un compte Kaggle gratuit (si pas déjà fait)
2. Allez sur le lien ci-dessus
3. Cliquez sur "Download" (télécharge un ZIP)
4. Décompressez dans le dossier : ai_datasets/
5. Renommez le dossier en : travel_images

Le dataset contient déjà :
- 6 catégories (beach, mountain, city, etc.)
- ~300-500 images par catégorie
- Déjà séparé en train/validation/test

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 OPTION 2 : Datasets alternatifs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. "Intel Image Classification"
   URL: https://www.kaggle.com/datasets/puneet6060/intel-image-classification
   Classes: buildings, forest, glacier, mountain, sea, street
   Images: ~25,000

2. "Tourist Spots Image Classification"
   URL: https://www.kaggle.com/datasets/msambare/tourist-spots-image-classification
   Classes: beach, desert, mountain, city, forest
   Images: ~5,000

3. "Places365" (Dataset académique officiel)
   URL: http://places2.csail.mit.edu/download.html
   Classes: 365 types de lieux
   Images: ~1.8 million (très gros)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 OPTION 3 : Créer votre propre mini-dataset (débutant)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pour un projet de démonstration/prototype :

1. Cherchez 50-100 images par catégorie sur Google Images
2. Organisez-les manuellement dans les dossiers
3. Entraînez le modèle (sera moins précis mais fonctionnel)

Structure requise :
ai_datasets/travel_images/
  ├── train/
  │   ├── beach/        (70% des images)
  │   ├── mountain/
  │   ├── city/
  │   ├── nature/
  │   ├── monument/
  │   └── restaurant/
  ├── validation/       (20% des images)
  │   └── ...
  └── test/            (10% des images)
      └── ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

def organize_downloaded_dataset():
    """
    Helper pour organiser un dataset téléchargé manuellement
    """
    print("\n🔧 ORGANISATION DU DATASET")
    print("=" * 60)
    
    if not Path(DATASET_DIR).exists():
        print("❌ Le dossier ai_datasets/travel_images n'existe pas encore.")
        print("   Téléchargez d'abord un dataset depuis Kaggle.\n")
        return
    
    # Vérifier la structure
    train_path = Path(DATASET_DIR) / 'train'
    if train_path.exists():
        categories = [d.name for d in train_path.iterdir() if d.is_dir()]
        print(f"✅ Dataset trouvé avec {len(categories)} catégories :")
        
        for cat in categories:
            train_count = len(list((train_path / cat).glob('*')))
            val_count = len(list((Path(DATASET_DIR) / 'validation' / cat).glob('*'))) if (Path(DATASET_DIR) / 'validation' / cat).exists() else 0
            test_count = len(list((Path(DATASET_DIR) / 'test' / cat).glob('*'))) if (Path(DATASET_DIR) / 'test' / cat).exists() else 0
            
            print(f"   📁 {cat:15} : {train_count:4} train, {val_count:4} val, {test_count:4} test")
        
        print("\n✅ Dataset prêt pour l'entraînement !")
        print("   Prochaine étape : python train_travel_classifier.py\n")
    else:
        print("❌ Structure de dataset invalide.")
        print("   Attendu : ai_datasets/travel_images/train/[categories]/")
        print("\n")


if __name__ == "__main__":
    print("\n📋 CHECKLIST")
    print("=" * 60)
    print("☐ 1. Télécharger un dataset depuis Kaggle")
    print("☐ 2. Décompresser dans ai_datasets/")
    print("☐ 3. Vérifier la structure")
    print("☐ 4. Lancer l'entraînement")
    print("=" * 60 + "\n")
    
    # Créer le dossier de base
    Path("ai_datasets").mkdir(exist_ok=True)
    
    # Vérifier si dataset existe déjà
    organize_downloaded_dataset()
    
    print("\n💡 CONSEILS")
    print("=" * 60)
    print("• Pour un projet académique, 500-1000 images/classe suffisent")
    print("• Utilisez Kaggle pour des datasets gratuits et de qualité")
    print("• L'entraînement prend 30-60 min sur CPU, 5-10 min sur GPU")
    print("• Accuracy attendue : 85-95% (selon qualité du dataset)")
    print("=" * 60 + "\n")


