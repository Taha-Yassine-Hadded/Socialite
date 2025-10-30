"""
Test amélioré avec 30 pays européens
"""
import sys
if 'ai_services.clip_service' in sys.modules:
    del sys.modules['ai_services.clip_service']

from ai_services.clip_service import ClipService

# Test avec 30 pays européens (Tour Eiffel devrait scorer plus haut pour France)
european_countries = [
    "France", "Germany", "Italy", "Spain", "United Kingdom",
    "Netherlands", "Belgium", "Switzerland", "Austria", "Portugal",
    "Greece", "Poland", "Czech Republic", "Hungary", "Sweden",
    "Denmark", "Norway", "Finland", "Ireland", "Croatia",
    "Romania", "Bulgaria", "Serbia", "Slovakia", "Slovenia",
    "Estonia", "Latvia", "Lithuania", "Luxembourg", "Malta"
]

image_path = r"C:\Users\dorsaf\Desktop\Projet Django\Socialite\test_images\eiffel.jpg"

print("🧪 Test CLIP amélioré - 30 pays européens")
print("=" * 60)

with open(image_path, 'rb') as f:
    image_bytes = f.read()

print(f"✅ Image chargée: {len(image_bytes)} bytes")
print(f"📊 Nombre de pays candidats: {len(european_countries)}")
print("\n⏳ Classification en cours...")

results = ClipService.zero_shot_countries(image_bytes, european_countries)

if results:
    print(f"\n✅ Classification terminée ! Top 10:\n")
    for i, r in enumerate(results[:10], 1):
        bar = "█" * int(r['score'] * 100)
        print(f"   {i:2d}. {r['country']:20s} {r['score']:.4f} {bar}")
    
    print(f"\n🎯 Pays détecté: {results[0]['country']} (confiance: {results[0]['score']:.2%})")
else:
    print("❌ Échec de la classification")
