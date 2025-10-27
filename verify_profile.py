"""
Script simple pour vérifier le profil MongoDB de l'utilisateur
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialite_project.settings')
django.setup()

from django.contrib.auth.models import User
from core.mongo import get_db

# Chercher l'utilisateur avec ID = 1
user = User.objects.get(id=1)

print("\n" + "="*60)
print(f"📋 PROFIL DE {user.first_name} {user.last_name}")
print("="*60 + "\n")

# Vérifier MongoDB
db = get_db()
mongo_profile = db.profiles.find_one({'user_id': user.id})

if mongo_profile:
    print("✅ DONNÉES MONGODB:")
    print("-" * 60)
    print(f"📧 Email         : {mongo_profile.get('email')}")
    print(f"👤 Nom complet   : {mongo_profile.get('first_name')} {mongo_profile.get('last_name')}")
    print(f"👥 Genre         : {mongo_profile.get('gender')}")
    print(f"💰 Budget voyage : {mongo_profile.get('travel_budget')}")
    print(f"🌍 Nationalité   : {mongo_profile.get('nationality')}")
    print(f"\n✈️  Types de voyage:")
    for t in mongo_profile.get('travel_type', []):
        print(f"   • {t}")
    print(f"\n🗣️  Langues parlées:")
    for lang in mongo_profile.get('languages', []):
        print(f"   • {lang}")
    print(f"\n🎯 Centres d'intérêt:")
    for interest in mongo_profile.get('interests', []):
        print(f"   • {interest}")
    
    visited = mongo_profile.get('visited_countries', [])
    print(f"\n🗺️  Pays visités ({len(visited)} pays):")
    if visited:
        for country in visited:
            print(f"   • {country}")
    else:
        print("   (Aucun pays visité pour le moment)")
    
    print("\n" + "="*60)
    print("✅ Dernière modification:", mongo_profile.get('_id').generation_time)
    print("="*60 + "\n")
else:
    print("❌ Aucun profil MongoDB trouvé!")

