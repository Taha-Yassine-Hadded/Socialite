"""
Script de test pour vérifier que CLIP fonctionne correctement
"""
import sys
from ai_services.clip_service import ClipService
from ai_services.countries import CONTINENTS, ALL_COUNTRIES

def test_clip():
    print("🧪 Test CLIP - Détection de pays")
    print("=" * 50)
    
    # Charger une image de test
    image_path = r"C:\Users\dorsaf\Desktop\Projet Django\Socialite\test_images\eiffel.jpg"
    
    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        print(f"✅ Image chargée: {len(image_bytes)} bytes")
        
        # Test 1: Prédire le continent
        print("\n📍 Test 1: Prédiction du continent...")
        continent = ClipService.predict_continent(image_bytes, CONTINENTS)
        print(f"   Continent prédit: {continent}")
        
        # Test 2: Classer les pays (Top 5)
        print("\n🌍 Test 2: Classification des pays (Top 5)...")
        results = ClipService.zero_shot_countries(image_bytes, ALL_COUNTRIES[:30])
        
        if results:
            print(f"   ✅ {len(results)} résultats obtenus")
            print("\n   Top 5:")
            for i, r in enumerate(results[:5], 1):
                print(f"   {i}. {r['country']:20s} - {r['score']:.4f}")
        else:
            print("   ❌ Aucun résultat (erreur)")
            
    except FileNotFoundError:
        print(f"❌ Erreur: Image introuvable à {image_path}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_clip()
