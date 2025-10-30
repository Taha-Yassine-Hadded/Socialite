# 🎓 GUIDE COMPLET : Classification d'images de voyage avec IA

## 📋 Vue d'ensemble

Ce guide vous explique comment créer et entraîner votre propre modèle IA pour classifier automatiquement les images de voyage.

---

## 🎯 Objectif

Créer un système IA qui :
- Analyse automatiquement les photos uploadées
- Détecte le type de destination (plage, montagne, ville, etc.)
- Génère des tags automatiques
- Améliore la recherche et l'organisation des photos

---

## 📊 Dataset requis

### **Option A : Dataset Kaggle (RECOMMANDÉ)**

**Dataset : "Intel Image Classification"**
- URL : https://www.kaggle.com/datasets/puneet6060/intel-image-classification
- Taille : ~25,000 images
- Classes : buildings, forest, glacier, mountain, sea, street
- Format : Déjà séparé en train/test

**Étapes :**
1. Créez un compte Kaggle gratuit
2. Téléchargez le ZIP (~300 MB)
3. Décompressez dans `ai_datasets/travel_images/`
4. Renommez les dossiers si nécessaire

### **Option B : Créer votre propre dataset**

**Pour un prototype/démo :**
- Minimum : 50-100 images par catégorie
- Recommandé : 300-500 images par catégorie
- Source : Google Images, vos propres photos, Unsplash

**Structure requise :**
```
ai_datasets/travel_images/
├── train/              (70% des images)
│   ├── beach/
│   │   ├── img001.jpg
│   │   ├── img002.jpg
│   │   └── ...
│   ├── mountain/
│   ├── city/
│   ├── nature/
│   ├── monument/
│   └── restaurant/
├── validation/         (20% des images)
│   ├── beach/
│   └── ...
└── test/              (10% des images)
    ├── beach/
    └── ...
```

---

## 🔧 Installation des dépendances

```bash
# Si pas déjà installé (normalement déjà fait avec Whisper)
pip install torch torchvision
pip install Pillow
```

---

## 📥 Étape 1 : Créer/Télécharger le dataset

### **Méthode automatique (Kaggle) :**

1. **Téléchargez le dataset depuis Kaggle**
2. **Décompressez-le**
3. **Organisez la structure :**

```bash
python download_public_dataset.py
```

Ce script vérifie la structure et affiche les statistiques.

---

## 🎓 Étape 2 : Entraîner le modèle

```bash
python train_travel_classifier.py
```

**Ce qui va se passer :**

```
🤖 ENTRAÎNEMENT DU CLASSIFICATEUR D'IMAGES DE VOYAGE
═══════════════════════════════════════════════════════

📂 Chargement des datasets...

📊 STATISTIQUES DU DATASET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Train        : 1800 images
   Validation   :  600 images
   Test         :  300 images
   TOTAL        : 2700 images
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧠 Création du modèle (Transfer Learning avec ResNet18)...
   ✅ Modèle créé avec 6 classes de sortie
   ✅ Basé sur ResNet18 (pré-entraîné sur ImageNet)

💻 Device utilisé : cpu
   ⚠️  Pas de GPU détecté, entraînement sur CPU (plus lent)

🚀 DÉBUT DE L'ENTRAÎNEMENT
══════════════════════════════════════════════════════════

Epoch 1/10
────────────────────────────────────────────────────────
   Train        Loss: 1.2345  Acc: 0.6500
   Validation   Loss: 0.9876  Acc: 0.7200
   ✅ Nouveau meilleur modèle ! Accuracy: 0.7200

Epoch 2/10
────────────────────────────────────────────────────────
   Train        Loss: 0.8765  Acc: 0.7800
   Validation   Loss: 0.7654  Acc: 0.8100
   ✅ Nouveau meilleur modèle ! Accuracy: 0.8100

...

Epoch 10/10
────────────────────────────────────────────────────────
   Train        Loss: 0.2345  Acc: 0.9200
   Validation   Loss: 0.3456  Acc: 0.8900

══════════════════════════════════════════════════════════
✅ ENTRAÎNEMENT TERMINÉ !
   Meilleure validation accuracy : 0.8900
══════════════════════════════════════════════════════════

🧪 TEST DU MODÈLE
══════════════════════════════════════════════════════════
   Test Accuracy : 0.8750 (87.50%)
══════════════════════════════════════════════════════════

💾 SAUVEGARDE DU MODÈLE
══════════════════════════════════════════════════════════
   Fichier : models/travel_classifier.pth
   Accuracy : 0.8750
   Classes : beach, city, monument, mountain, nature, restaurant
══════════════════════════════════════════════════════════

✅ Modèle sauvegardé avec succès !

🎉 PROCESSUS TERMINÉ !
   Vous pouvez maintenant intégrer le modèle dans Django.
```

**⏱️ Temps d'entraînement :**
- CPU : 30-60 minutes
- GPU (NVIDIA) : 5-10 minutes

---

## 🔗 Étape 3 : Intégrer dans Django

Le modèle sera automatiquement utilisé quand vous uploadez une image !

**Modifications déjà faites dans :**
- `core/ai_services.py` : Fonctions de classification
- `core/views.py` : (à ajouter) Appel automatique lors de l'upload
- `core/models.py` : (à ajouter) Champs pour stocker la catégorie

---

## 📊 Résultats attendus

**Accuracy attendue :**
- Dataset petit (500 images) : 70-80%
- Dataset moyen (2000 images) : 85-90%
- Dataset large (10000+ images) : 90-95%

**Exemples de prédictions :**
```
Photo de plage     → "Plage" (92% confiance)
Photo de montagne  → "Montagne" (88% confiance)
Photo de ville     → "Ville" (85% confiance)
```

---

## 🚀 Utilisation dans l'application

Une fois le modèle entraîné, à chaque upload d'image :

1. L'image est sauvegardée dans Django
2. Le modèle classifie automatiquement l'image
3. La catégorie et les tags sont sauvegardés
4. L'utilisateur voit les tags suggérés
5. Recherche facilitée par catégorie

---

## 📝 CHECKLIST COMPLÈTE

```
☐ 1. Télécharger dataset depuis Kaggle
☐ 2. Décompresser dans ai_datasets/travel_images/
☐ 3. Vérifier structure : python download_public_dataset.py
☐ 4. Entraîner modèle : python train_travel_classifier.py
☐ 5. Vérifier : models/travel_classifier.pth créé
☐ 6. Ajouter champs dans models.py
☐ 7. Modifier create_post dans views.py
☐ 8. Tester avec upload d'image
☐ 9. Vérifier logs de classification
☐ 10. Voir les tags automatiques !
```

---

## 💡 Différence avec Whisper

| Aspect | Whisper (Audio) | Classifier (Images) |
|--------|----------------|---------------------|
| **Dataset** | ❌ Pré-entraîné OpenAI | ✅ **VOTRE dataset** |
| **Entraînement** | ❌ Déjà fait | ✅ **VOUS entraînez** |
| **Temps setup** | 10 minutes | 2-3 heures |
| **Personnalisation** | ❌ Fixe | ✅ Total contrôle |
| **Apprentissage ML** | ⭐⭐ | ⭐⭐⭐⭐⭐ |

**C'est ICI que vous apprenez vraiment le Machine Learning ! 🎓**

---

## 🎯 Prochaines améliorations possibles

1. Ajouter plus de catégories
2. Augmenter la taille du dataset
3. Fine-tuner plus longtemps
4. Utiliser ResNet50 au lieu de ResNet18
5. Ajouter détection de plusieurs éléments par image


