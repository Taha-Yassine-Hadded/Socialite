"""
Script pour vérifier les données du profil dans SQLite et MongoDB
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialite_project.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile
from core.mongo import get_db

print("\n" + "="*60)
print("🔍 VÉRIFICATION DES DONNÉES DU PROFIL")
print("="*60 + "\n")

# Demander l'email de l'utilisateur
email = input("Entrez l'email de l'utilisateur à vérifier : ").strip()

try:
    # 1. Vérifier les données SQLite (Django)
    user = User.objects.get(email=email)
    print(f"\n✅ UTILISATEUR TROUVÉ DANS SQLITE (Django)")
    print("-" * 60)
    print(f"📧 Email      : {user.email}")
    print(f"👤 Username   : {user.username}")
    print(f"📝 Prénom     : {user.first_name}")
    print(f"📝 Nom        : {user.last_name}")
    print(f"🆔 User ID    : {user.id}")
    
    # Vérifier le profil UserProfile
    try:
        profile = user.profile
        print(f"\n✅ PROFIL DJANGO (UserProfile) TROUVÉ")
        print("-" * 60)
        print(f"🔗 Slug       : {profile.slug}")
        print(f"📝 Bio        : {profile.bio[:50] if profile.bio else 'Non défini'}...")
        print(f"📍 Location   : {profile.location or 'Non défini'}")
        print(f"🎂 Naissance  : {profile.birth_date or 'Non défini'}")
        print(f"🖼️  Avatar     : {'✅ Oui' if profile.avatar else '❌ Non'}")
        print(f"🖼️  Couverture : {'✅ Oui' if profile.cover_image else '❌ Non'}")
        print(f"✈️  Style voyage : {profile.travel_style or 'Non défini'}")
    except UserProfile.DoesNotExist:
        print(f"\n❌ AUCUN PROFIL DJANGO TROUVÉ POUR CET UTILISATEUR")
    
    # 2. Vérifier les données MongoDB
    db = get_db()
    mongo_profile = db.profiles.find_one({'user_id': user.id})
    
    if mongo_profile:
        print(f"\n✅ PROFIL MONGODB TROUVÉ")
        print("-" * 60)
        print(f"📧 Email      : {mongo_profile.get('email', 'Non défini')}")
        print(f"📝 Prénom     : {mongo_profile.get('first_name', 'Non défini')}")
        print(f"📝 Nom        : {mongo_profile.get('last_name', 'Non défini')}")
        print(f"👥 Genre      : {mongo_profile.get('gender', 'Non défini')}")
        print(f"💰 Budget     : {mongo_profile.get('travel_budget', 'Non défini')}")
        print(f"🌍 Nationalité : {mongo_profile.get('nationality', 'Non défini')}")
        print(f"✈️  Types voyage : {', '.join(mongo_profile.get('travel_type', [])) or 'Aucun'}")
        print(f"🗣️  Langues    : {', '.join(mongo_profile.get('languages', [])) or 'Aucune'}")
        print(f"🎯 Intérêts   : {', '.join(mongo_profile.get('interests', [])) or 'Aucun'}")
        print(f"🗺️  Pays visités : {len(mongo_profile.get('visited_countries', []))} pays")
        if mongo_profile.get('visited_countries'):
            print(f"   → {', '.join(mongo_profile.get('visited_countries', []))}")
    else:
        print(f"\n❌ AUCUN PROFIL MONGODB TROUVÉ POUR CET UTILISATEUR")
        print(f"   Le profil sera créé automatiquement lors de la prochaine modification")
    
    print("\n" + "="*60)
    print("✅ VÉRIFICATION TERMINÉE")
    print("="*60 + "\n")
    
except User.DoesNotExist:
    print(f"\n❌ ERREUR : Aucun utilisateur trouvé avec l'email '{email}'")
    print("\n📋 Utilisateurs disponibles :")
    print("-" * 60)
    for u in User.objects.all():
        print(f"   • {u.email} (ID: {u.id})")
    print()

except Exception as e:
    print(f"\n❌ ERREUR : {str(e)}")
    import traceback
    traceback.print_exc()

