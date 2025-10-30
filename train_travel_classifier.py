"""
Script d'entraînement pour le classificateur d'images de voyage
Utilise Transfer Learning avec ResNet18 pré-entraîné sur ImageNet
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
import time
import copy
from pathlib import Path
import json

# Configuration
DATASET_DIR = "ai_datasets/travel_images"
MODEL_SAVE_PATH = "models/travel_classifier.pth"
BATCH_SIZE = 32
NUM_EPOCHS = 10
LEARNING_RATE = 0.001

# Catégories (doit correspondre aux dossiers)
CLASSES = ['beach', 'city', 'monument', 'mountain', 'nature', 'restaurant']

def get_data_transforms():
    """
    Transformations pour augmentation de données
    """
    data_transforms = {
        'train': transforms.Compose([
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(10),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'validation': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'test': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
    }
    return data_transforms


def load_datasets():
    """
    Charge les datasets train/validation/test
    """
    print("📂 Chargement des datasets...")
    
    data_transforms = get_data_transforms()
    
    image_datasets = {
        x: datasets.ImageFolder(
            Path(DATASET_DIR) / x,
            data_transforms[x]
        )
        for x in ['train', 'validation', 'test']
    }
    
    dataloaders = {
        x: DataLoader(
            image_datasets[x],
            batch_size=BATCH_SIZE,
            shuffle=(x == 'train'),
            num_workers=0  # 0 pour Windows, augmentez sur Linux
        )
        for x in ['train', 'validation', 'test']
    }
    
    dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'validation', 'test']}
    
    print("\n📊 STATISTIQUES DU DATASET")
    print("━" * 60)
    for split, size in dataset_sizes.items():
        print(f"   {split.capitalize():12} : {size:4} images")
    print(f"   {'TOTAL':12} : {sum(dataset_sizes.values()):4} images")
    print("━" * 60 + "\n")
    
    return dataloaders, dataset_sizes, image_datasets['train'].classes


def create_model(num_classes):
    """
    Crée le modèle avec Transfer Learning (ResNet18)
    """
    print("🧠 Création du modèle (Transfer Learning avec ResNet18)...")
    
    # Charger ResNet18 pré-entraîné sur ImageNet
    model = models.resnet18(pretrained=True)
    
    # Geler les couches pré-entraînées (optionnel)
    # for param in model.parameters():
    #     param.requires_grad = False
    
    # Remplacer la dernière couche pour nos 6 classes
    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, num_classes)
    
    print(f"   ✅ Modèle créé avec {num_classes} classes de sortie")
    print(f"   ✅ Basé sur ResNet18 (pré-entraîné sur ImageNet)\n")
    
    return model


def train_model(model, dataloaders, dataset_sizes, num_epochs=10):
    """
    Entraîne le modèle
    """
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"💻 Device utilisé : {device}")
    if device.type == 'cpu':
        print("   ⚠️  Pas de GPU détecté, entraînement sur CPU (plus lent)")
    print()
    
    model = model.to(device)
    
    # Loss et optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=7, gamma=0.1)
    
    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0
    
    print("🚀 DÉBUT DE L'ENTRAÎNEMENT")
    print("=" * 60 + "\n")
    
    for epoch in range(num_epochs):
        print(f"Epoch {epoch+1}/{num_epochs}")
        print("-" * 60)
        
        # Chaque epoch a une phase d'entraînement et de validation
        for phase in ['train', 'validation']:
            if phase == 'train':
                model.train()
            else:
                model.eval()
            
            running_loss = 0.0
            running_corrects = 0
            
            # Itérer sur les données
            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)
                
                optimizer.zero_grad()
                
                # Forward
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)
                    
                    # Backward + optimize seulement en train
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()
                
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
            
            if phase == 'train':
                scheduler.step()
            
            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]
            
            print(f"   {phase.capitalize():12} Loss: {epoch_loss:.4f}  Acc: {epoch_acc:.4f}")
            
            # Sauvegarder le meilleur modèle
            if phase == 'validation' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())
                print(f"   ✅ Nouveau meilleur modèle ! Accuracy: {best_acc:.4f}")
        
        print()
    
    print("=" * 60)
    print(f"✅ ENTRAÎNEMENT TERMINÉ !")
    print(f"   Meilleure validation accuracy : {best_acc:.4f}")
    print("=" * 60 + "\n")
    
    # Charger le meilleur modèle
    model.load_state_dict(best_model_wts)
    return model, best_acc


def test_model(model, dataloaders):
    """
    Teste le modèle sur le test set
    """
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    model.eval()
    
    running_corrects = 0
    total = 0
    
    print("🧪 TEST DU MODÈLE")
    print("=" * 60)
    
    with torch.no_grad():
        for inputs, labels in dataloaders['test']:
            inputs = inputs.to(device)
            labels = labels.to(device)
            
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            
            running_corrects += torch.sum(preds == labels.data)
            total += labels.size(0)
    
    test_acc = running_corrects.double() / total
    print(f"   Test Accuracy : {test_acc:.4f} ({test_acc*100:.2f}%)")
    print("=" * 60 + "\n")
    
    return test_acc


def save_model(model, class_names, accuracy):
    """
    Sauvegarde le modèle entraîné
    """
    # Créer le dossier models
    Path("models").mkdir(exist_ok=True)
    
    # Sauvegarder le modèle
    model_data = {
        'model_state_dict': model.state_dict(),
        'class_names': class_names,
        'num_classes': len(class_names),
        'accuracy': float(accuracy),
        'model_architecture': 'ResNet18',
        'input_size': 224,
        'trained_date': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    torch.save(model_data, MODEL_SAVE_PATH)
    
    print("💾 SAUVEGARDE DU MODÈLE")
    print("=" * 60)
    print(f"   Fichier : {MODEL_SAVE_PATH}")
    print(f"   Accuracy : {accuracy:.4f}")
    print(f"   Classes : {', '.join(class_names)}")
    print("=" * 60 + "\n")
    
    # Sauvegarder aussi les métadonnées en JSON
    metadata = {
        'class_names': class_names,
        'num_classes': len(class_names),
        'accuracy': float(accuracy),
        'model_architecture': 'ResNet18',
        'trained_date': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open('models/travel_classifier_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("✅ Modèle sauvegardé avec succès !\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 ENTRAÎNEMENT DU CLASSIFICATEUR D'IMAGES DE VOYAGE")
    print("="*60 + "\n")
    
    # Vérifier que le dataset existe
    if not Path(DATASET_DIR).exists():
        print("❌ ERREUR : Le dataset n'existe pas !")
        print("   Exécutez d'abord : python create_travel_dataset.py")
        exit(1)
    
    # Charger les données
    dataloaders, dataset_sizes, class_names = load_datasets()
    
    # Créer le modèle
    model = create_model(len(class_names))
    
    # Entraîner
    model, best_acc = train_model(model, dataloaders, dataset_sizes, NUM_EPOCHS)
    
    # Tester
    test_acc = test_model(model, dataloaders)
    
    # Sauvegarder
    save_model(model, class_names, test_acc)
    
    print("🎉 PROCESSUS TERMINÉ !")
    print("   Vous pouvez maintenant intégrer le modèle dans Django.\n")


