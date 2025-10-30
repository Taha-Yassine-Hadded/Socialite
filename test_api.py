"""
Test amélioré de l'API de détection de pays avec requests
Permet de tester plusieurs images et d'afficher des résultats détaillés
"""
import requests
import os
import json
import argparse
import time
from datetime import datetime

# Configuration
url = "http://127.0.0.1:8000/api/ai/detect-country/"
test_images_dir = r"C:\Users\dorsaf\Desktop\Projet Django\Socialite\test_images"

# Couleurs pour le terminal
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def test_single_image(image_path, verbose=False):
    """Teste l'API avec une seule image"""
    print(f"{Colors.BOLD}🧪 Test API avec image:{Colors.END} {os.path.basename(image_path)}")
    
    try:
        start_time = time.time()
        with open(image_path, 'rb') as f:
            files = {'image': f}
            print("⏳ Envoi de la requête...")
            response = requests.post(url, files=files, timeout=60)
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  Temps de réponse: {elapsed_time:.2f} secondes")
        print(f"📊 Status Code: {response.status_code}\n")
        
        if response.status_code == 200:
            data = response.json()
            
            # Affichage des résultats principaux
            print(f"{Colors.GREEN}✅ Réponse reçue:{Colors.END}")
            print(f"   {Colors.BOLD}Méthode:{Colors.END} {data.get('method')}")
            print(f"   {Colors.BOLD}Pays:{Colors.END} {data.get('country')}")
            print(f"   {Colors.BOLD}Confiance:{Colors.END} {data.get('confidence'):.2%}")
            
            # Affichage des détails spécifiques selon la méthode
            if data.get('method') == 'landmark' and 'landmark' in data:
                print(f"   {Colors.BOLD}🏛️  Landmark:{Colors.END} {data['landmark']}")
            
            elif data.get('method') == 'ocr' and 'detected_text' in data:
                print(f"   {Colors.BOLD}📝 Texte détecté:{Colors.END} {data['detected_text'][:100]}...")
            
            elif data.get('method') == 'exif' and 'coordinates' in data:
                print(f"   {Colors.BOLD}📍 Coordonnées:{Colors.END} {data['coordinates']}")
            
            elif data.get('method') == 'clip' and 'predicted_continent' in data:
                print(f"   {Colors.BOLD}🌍 Continent:{Colors.END} {data['predicted_continent']}")
            
            # Affichage des candidats
            if 'candidates' in data and data['candidates']:
                print(f"\n   {Colors.BOLD}Top candidats:{Colors.END}")
                for i, candidate in enumerate(data.get('candidates', [])[:5], 1):
                    print(f"      {i}. {candidate['country']:20s} {candidate['score']:.4f}")
            
            # Affichage du JSON complet en mode verbose
            if verbose:
                print(f"\n{Colors.BLUE}📋 Réponse JSON complète:{Colors.END}")
                print(json.dumps(data, indent=2))
                
            return data
        else:
            print(f"{Colors.RED}❌ Erreur: {response.text}{Colors.END}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}❌ Erreur: Impossible de se connecter au serveur{Colors.END}")
        print("   Assurez-vous que le serveur Django tourne: python manage.py runserver")
    except FileNotFoundError:
        print(f"{Colors.RED}❌ Erreur: Image introuvable à {image_path}{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}❌ Erreur: {e}{Colors.END}")
    
    return None

def test_multiple_images(directory=None, verbose=False):
    """Teste l'API avec toutes les images d'un répertoire"""
    if directory is None:
        directory = test_images_dir
    
    if not os.path.exists(directory):
        print(f"{Colors.RED}❌ Erreur: Répertoire {directory} introuvable{Colors.END}")
        return
    
    image_files = [f for f in os.listdir(directory) 
                  if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
    
    if not image_files:
        print(f"{Colors.YELLOW}⚠️ Aucune image trouvée dans {directory}{Colors.END}")
        return
    
    print(f"{Colors.BOLD}🧪 Test API avec {len(image_files)} images{Colors.END}")
    print("=" * 60)
    
    results = []
    methods_count = {'landmark': 0, 'ocr': 0, 'exif': 0, 'clip': 0}
    
    for i, img_file in enumerate(image_files, 1):
        print(f"\n{Colors.BOLD}Image {i}/{len(image_files)}: {img_file}{Colors.END}")
        print("-" * 60)
        
        img_path = os.path.join(directory, img_file)
        result = test_single_image(img_path, verbose)
        
        if result:
            results.append({
                'image': img_file,
                'country': result.get('country'),
                'method': result.get('method'),
                'confidence': result.get('confidence')
            })
            
            # Comptage des méthodes utilisées
            method = result.get('method')
            if method in methods_count:
                methods_count[method] += 1
        
        print("-" * 60)
    
    # Affichage du résumé
    print(f"\n{Colors.BOLD}📊 Résumé des tests:{Colors.END}")
    print(f"   Images testées: {len(results)}/{len(image_files)}")
    print(f"   Méthodes utilisées:")
    for method, count in methods_count.items():
        if count > 0:
            percent = (count / len(results)) * 100 if results else 0
            print(f"      - {method}: {count} ({percent:.1f}%)")

def main():
    parser = argparse.ArgumentParser(description="Test de l'API de détection de pays")
    parser.add_argument('-i', '--image', help='Chemin vers une image spécifique à tester')
    parser.add_argument('-d', '--directory', help='Répertoire contenant les images à tester')
    parser.add_argument('-v', '--verbose', action='store_true', help='Afficher les détails complets')
    args = parser.parse_args()
    
    print(f"{Colors.BOLD}🌍 TEST API DÉTECTION DE PAYS{Colors.END}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL: {url}")
    print("=" * 60)
    
    if args.image:
        test_single_image(args.image, args.verbose)
    else:
        test_multiple_images(args.directory, args.verbose)

if __name__ == "__main__":
    main()