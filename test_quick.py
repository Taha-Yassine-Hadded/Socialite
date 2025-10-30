import sys
# Forcer le rechargement
if 'ai_services.clip_service' in sys.modules:
    del sys.modules['ai_services.clip_service']
if 'ai_services.countries' in sys.modules:
    del sys.modules['ai_services.countries']

from ai_services.clip_service import ClipService

# Test rapide
image_path = r"C:\Users\dorsaf\Desktop\Projet Django\Socialite\test_images\eiffel.jpg"
with open(image_path, 'rb') as f:
    image_bytes = f.read()

print("Test CLIP...")
results = ClipService.zero_shot_countries(image_bytes, ["France", "Germany", "Italy", "Spain", "Belgium"])
if results:
    print("✅ Succès!")
    for r in results[:3]:
        print(f"   {r['country']}: {r['score']:.4f}")
else:
    print("❌ Échec")
