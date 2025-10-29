# 🌍 Socialite

## 📖 Overview
Socialite is a Django-based social platform that inspires users to explore the world and share their travel experiences. Connect with others, create communities, and engage through posts, photos, and discussions about global destinations, fostering cultural exchange among travelers worldwide.

## ✨ Features
- **💬 Real-Time Interaction**: Live chat and instant WebSocket notifications.
- **🔒 User Authentication**: Secure access with Django authentication.
- **🛠️ Admin Panel**: Manage users, posts, and communities via Django Admin.
- **🌐 Community Building**: Share travel stories, photos, and tips in communities.
- **📱 Responsive Design**: Sleek UI with Tailwind CSS for all devices.

## 🛠️ Technologies
- **Backend**: Django, MongoDB
- **Frontend**: Django Templates, Tailwind CSS
- **Real-Time**: WebSockets
- **Version Control**: Git, GitHub

## 🚀 Installation
1. Clone the repository:
   ```
   git clone https://github.com/Taha-Yassine-Hadded/Socialite.git
   ```
2. Navigate to the project directory:
   ```
   cd Socialite
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set up MongoDB and configure in `settings.py`.
5. Run migrations:
   ```
   python manage.py migrate
   ```
6. Start the server:
   ```
   python manage.py runserver
   ```

## 📋 Usage
- 🧑‍💻 Register or log in to create a profile.
- 🌎 Explore communities and share posts.
- 💬 Use real-time chat for discussions.
- 🔧 Admins can manage content via Django Admin.

---

## 🤖 Quickstart IA (Dataset + Modèle)

- Composants IA inclus:
  - Whisper (transcription audio/vidéo) → champs `voice_transcription`, `detected_language` dans `Post`.
  - Classifieur images voyage (ResNet18 fine‑tuned) → `image_category`, `image_category_fr`, `image_confidence`, `image_tags`.

### 1) Récupérer le modèle `.pth`
Option A (recommandé): via script
```
# PowerShell (Windows)
$env:TRAVEL_MODEL_URL="https://<votre-hébergement>/travel_classifier.pth"
# facultatif
$env:TRAVEL_MODEL_SHA256="<checksum_sha256>"
python download_model.py
```
Le fichier sera enregistré dans `models/travel_classifier.pth`.

Option B: Git LFS (si activé sur votre repo)
```
git lfs install
git lfs pull
```

### 2) Structure du dataset (facultatif pour ré‑entraîner)
Voir `ai_datasets/README.md`. Structure attendue:
```
travel_images/
  train/       buildings/ forest/ glacier/ mountain/ sea/ street/
  validation/  buildings/ forest/ glacier/ mountain/ sea/ street/
  test/        buildings/ forest/ glacier/ mountain/ sea/ street/
```
- Téléchargement public: `python download_public_dataset.py`
- Mini‑dataset de test: `python create_mini_dataset.py`

### 3) Ré‑entraîner le modèle (optionnel)
```
python train_travel_classifier.py
# sorties: models/travel_classifier.pth + models/travel_classifier_metadata.json
```

### 4) Lancer l’application
```
python manage.py migrate
python manage.py runserver
```
- À la création d’un post: la transcription Whisper et la classification d’image s’exécutent automatiquement si médias fournis.

### 5) Notes & dépendances
- FFmpeg requis pour Whisper (Windows: chemins gérés dans `core/ai_services.py`).
- Ne versionnez pas `ai_datasets/`, `media/`, `venv/`, `models/*.pth`. Voir `.gitignore`.
- Métadonnées du modèle: `models/travel_classifier_metadata.json` (classes, accuracy, version).

---