from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.db import IntegrityError
from .mongo import get_db
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
import uuid
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required 
from django.contrib import messages
from .forms import UserEditForm, ProfileEditForm, CustomPasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from .models import Post, Comment, Reaction, Share, UserProfile, Avis, AnalyticsEvent, Story, StoryView
from django.db.utils import OperationalError as DBOperationalError
from .ai_services import transcribe_voice_note, classify_travel_image, get_image_tags
import json
import stripe
import requests
from django.conf import settings
from decimal import Decimal
from core.utils.subscription import can_user_perform_action, increment_usage
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import Subscription, UsageQuota, PaymentHistory
from core.ml_models.sentiment_analyzer import sentiment_analyzer  # Add this import at the top
import logging

# Liste des intérêts pour le formulaire
INTERESTS = ['adventure', 'culture', 'gastronomy', 'nature', 'sport', 'relaxation']

# Liste des types de voyage
TRAVEL_TYPES = [
    ('solo', 'Solo'),
    ('group', 'Group'),
    ('couple', 'Couple'),
    ('friends', 'Friends')
]

# Liste des langues du monde (basée sur ISO 639-1 et langues courantes)
LANGUAGES = [
    ('af', 'Afrikaans'), ('sq', 'Albanian'), ('am', 'Amharic'), ('ar', 'Arabic'), 
    ('hy', 'Armenian'), ('az', 'Azerbaijani'), ('eu', 'Basque'), ('be', 'Belarusian'), 
    ('bn', 'Bengali'), ('bs', 'Bosnian'), ('bg', 'Bulgarian'), ('my', 'Burmese'), 
    ('ca', 'Catalan'), ('zh', 'Chinese'), ('hr', 'Croatian'), ('cs', 'Czech'), 
    ('da', 'Danish'), ('nl', 'Dutch'), ('en', 'English'), ('et', 'Estonian'), 
    ('fi', 'Finnish'), ('fr', 'French'), ('gl', 'Galician'), ('ka', 'Georgian'), 
    ('de', 'German'), ('el', 'Greek'), ('gu', 'Gujarati'), ('ha', 'Hausa'), 
    ('he', 'Hebrew'), ('hi', 'Hindi'), ('hu', 'Hungarian'), ('is', 'Icelandic'), 
    ('ig', 'Igbo'), ('id', 'Indonesian'), ('ga', 'Irish'), ('it', 'Italian'), 
    ('ja', 'Japanese'), ('kn', 'Kannada'), ('kk', 'Kazakh'), ('km', 'Khmer'), 
    ('ko', 'Korean'), ('ky', 'Kyrgyz'), ('lo', 'Lao'), ('lv', 'Latvian'), 
    ('lt', 'Lithuanian'), ('mk', 'Macedonian'), ('mg', 'Malagasy'), ('ms', 'Malay'), 
    ('ml', 'Malayalam'), ('mt', 'Maltese'), ('mi', 'Maori'), ('mr', 'Marathi'), 
    ('mn', 'Mongolian'), ('ne', 'Nepali'), ('no', 'Norwegian'), ('or', 'Odia'), 
    ('ps', 'Pashto'), ('fa', 'Persian'), ('pl', 'Polish'), ('pt', 'Portuguese'), 
    ('pa', 'Punjabi'), ('ro', 'Romanian'), ('ru', 'Russian'), ('sr', 'Serbian'), 
    ('sn', 'Shona'), ('sd', 'Sindhi'), ('si', 'Sinhala'), ('sk', 'Slovak'), 
    ('sl', 'Slovenian'), ('so', 'Somali'), ('es', 'Spanish'), ('su', 'Sundanese'), 
    ('sw', 'Swahili'), ('sv', 'Swedish'), ('tl', 'Tagalog'), ('ta', 'Tamil'), 
    ('te', 'Telugu'), ('th', 'Thai'), ('tr', 'Turkish'), ('uk', 'Ukrainian'), 
    ('ur', 'Urdu'), ('uz', 'Uzbek'), ('vi', 'Vietnamese'), ('cy', 'Welsh'), 
    ('xh', 'Xhosa'), ('yi', 'Yiddish'), ('yo', 'Yoruba'), ('zu', 'Zulu')
]

# Liste des pays du monde (basée sur ISO 3166-1 alpha-2)
COUNTRIES = [
    ('AF', 'Afghanistan'), ('AL', 'Albania'), ('DZ', 'Algeria'), ('AD', 'Andorra'),
    ('AO', 'Angola'), ('AG', 'Antigua and Barbuda'), ('AR', 'Argentina'), ('AM', 'Armenia'),
    ('AU', 'Australia'), ('AT', 'Austria'), ('AZ', 'Azerbaijan'), ('BS', 'Bahamas'),
    ('BH', 'Bahrain'), ('BD', 'Bangladesh'), ('BB', 'Barbados'), ('BY', 'Belarus'),
    ('BE', 'Belgium'), ('BZ', 'Belize'), ('BJ', 'Benin'), ('BT', 'Bhutan'),
    ('BO', 'Bolivia'), ('BA', 'Bosnia and Herzegovina'), ('BW', 'Botswana'), ('BR', 'Brazil'),
    ('BN', 'Brunei'), ('BG', 'Bulgaria'), ('BF', 'Burkina Faso'), ('BI', 'Burundi'),
    ('KH', 'Cambodia'), ('CM', 'Cameroon'), ('CA', 'Canada'), ('CV', 'Cape Verde'),
    ('CF', 'Central African Republic'), ('TD', 'Chad'), ('CL', 'Chile'), ('CN', 'China'),
    ('CO', 'Colombia'), ('KM', 'Comoros'), ('CG', 'Congo'), ('CD', 'Congo, Democratic Republic'),
    ('CR', 'Costa Rica'), ('HR', 'Croatia'), ('CU', 'Cuba'), ('CY', 'Cyprus'),
    ('CZ', 'Czech Republic'), ('DK', 'Denmark'), ('DJ', 'Djibouti'), ('DM', 'Dominica'),
    ('DO', 'Dominican Republic'), ('EC', 'Ecuador'), ('EG', 'Egypt'), ('SV', 'El Salvador'),
    ('GQ', 'Equatorial Guinea'), ('ER', 'Eritrea'), ('EE', 'Estonia'), ('ET', 'Ethiopia'),
    ('FJ', 'Fiji'), ('FI', 'Finland'), ('FR', 'France'), ('GA', 'Gabon'),
    ('GM', 'Gambia'), ('GE', 'Georgia'), ('DE', 'Germany'), ('GH', 'Ghana'),
    ('GR', 'Greece'), ('GD', 'Grenada'), ('GT', 'Guatemala'), ('GN', 'Guinea'),
    ('GW', 'Guinea-Bissau'), ('GY', 'Guyana'), ('HT', 'Haiti'), ('HN', 'Honduras'),
    ('HU', 'Hungary'), ('IS', 'Iceland'), ('IN', 'India'), ('ID', 'Indonesia'),
    ('IR', 'Iran'), ('IQ', 'Iraq'), ('IE', 'Ireland'), ('IL', 'Israel'),
    ('IT', 'Italy'), ('JM', 'Jamaica'), ('JP', 'Japan'), ('JO', 'Jordan'),
    ('KZ', 'Kazakhstan'), ('KE', 'Kenya'), ('KI', 'Kiribati'), ('KP', 'North Korea'),
    ('KR', 'South Korea'), ('KW', 'Kuwait'), ('KG', 'Kyrgyzstan'), ('LA', 'Laos'),
    ('LV', 'Latvia'), ('LB', 'Lebanon'), ('LS', 'Lesotho'), ('LR', 'Liberia'),
    ('LY', 'Libya'), ('LI', 'Liechtenstein'), ('LT', 'Lithuania'), ('LU', 'Luxembourg'),
    ('MG', 'Madagascar'), ('MW', 'Malawi'), ('MY', 'Malaysia'), ('MV', 'Maldives'),
    ('ML', 'Mali'), ('MT', 'Malta'), ('MH', 'Marshall Islands'), ('MR', 'Mauritania'),
    ('MU', 'Mauritius'), ('MX', 'Mexico'), ('FM', 'Micronesia'), ('MD', 'Moldova'),
    ('MC', 'Monaco'), ('MN', 'Mongolia'), ('ME', 'Montenegro'), ('MA', 'Morocco'),
    ('MZ', 'Mozambique'), ('MM', 'Myanmar'), ('NA', 'Namibia'), ('NR', 'Nauru'),
    ('NP', 'Nepal'), ('NL', 'Netherlands'), ('NZ', 'New Zealand'), ('NI', 'Nicaragua'),
    ('NE', 'Niger'), ('NG', 'Nigeria'), ('NO', 'Norway'), ('OM', 'Oman'),
    ('PK', 'Pakistan'), ('PW', 'Palau'), ('PA', 'Panama'), ('PG', 'Papua New Guinea'),
    ('PY', 'Paraguay'), ('PE', 'Peru'), ('PH', 'Philippines'), ('PL', 'Poland'),
    ('PT', 'Portugal'), ('QA', 'Qatar'), ('RO', 'Romania'), ('RU', 'Russia'),
    ('RW', 'Rwanda'), ('KN', 'Saint Kitts and Nevis'), ('LC', 'Saint Lucia'),
    ('VC', 'Saint Vincent and the Grenadines'), ('WS', 'Samoa'), ('SM', 'San Marino'),
    ('ST', 'Sao Tome and Principe'), ('SA', 'Saudi Arabia'), ('SN', 'Senegal'),
    ('RS', 'Serbia'), ('SC', 'Seychelles'), ('SL', 'Sierra Leone'), ('SG', 'Singapore'),
    ('SK', 'Slovakia'), ('SI', 'Slovenia'), ('SB', 'Solomon Islands'), ('SO', 'Somalia'),
    ('ZA', 'South Africa'), ('SS', 'South Sudan'), ('ES', 'Spain'), ('LK', 'Sri Lanka'),
    ('SD', 'Sudan'), ('SR', 'Suriname'), ('SE', 'Sweden'), ('CH', 'Switzerland'),
    ('SY', 'Syria'), ('TW', 'Taiwan'), ('TJ', 'Tajikistan'), ('TZ', 'Tanzania'),
    ('TH', 'Thailand'), ('TL', 'Timor-Leste'), ('TG', 'Togo'), ('TO', 'Tonga'),
    ('TT', 'Trinidad and Tobago'), ('TN', 'Tunisia'), ('TR', 'Turkey'), ('TM', 'Turkmenistan'),
    ('TV', 'Tuvalu'), ('UG', 'Uganda'), ('UA', 'Ukraine'), ('AE', 'United Arab Emirates'),
    ('GB', 'United Kingdom'), ('US', 'United States'), ('UY', 'Uruguay'), ('UZ', 'Uzbekistan'),
    ('VU', 'Vanuatu'), ('VE', 'Venezuela'), ('VN', 'Vietnam'), ('YE', 'Yemen'),
    ('ZM', 'Zambia'), ('ZW', 'Zimbabwe')
]

def format_follower_count(count):
    """Format follower count (e.g., 100000 -> 100K, 1000000 -> 1M)."""
    if count >= 1_000_000:
        return f"{count // 1_000_000}M"
    elif count >= 1_000:
        return f"{count // 1_000}K"
    return str(count)

def calculate_similarity(user_profile, other_profile):
    """Calculate similarity score between two user profiles."""
    score = 0
    # Travel types
    user_travel_types = set(user_profile.get('travel_type', []))
    other_travel_types = set(other_profile.get('travel_type', []))
    score += len(user_travel_types.intersection(other_travel_types)) * 2
    
    # Languages
    user_languages = set(user_profile.get('languages', []))
    other_languages = set(other_profile.get('languages', []))
    score += len(user_languages.intersection(other_languages))
    
    # Nationality
    if user_profile.get('nationality') == other_profile.get('nationality'):
        score += 5
    
    # Interests
    user_interests = set(user_profile.get('interests', []))
    other_interests = set(other_profile.get('interests', []))
    score += len(user_interests.intersection(other_interests)) * 3
    
    return score

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    """Returns the connected user's info"""
    user = request.user
    
    # Fetch MongoDB profile
    db = get_db()
    profile = db.profiles.find_one({'user_id': user.id})
    
    return JsonResponse({
        'success': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile_image': profile.get('profile_image') if profile else None,
            'date_of_birth': profile.get('date_of_birth') if profile else None,
            'is_staff': user.is_staff,
            'travel_type': profile.get('travel_type') if profile else None,
            'travel_budget': profile.get('travel_budget') if profile else None,
            'gender': profile.get('gender') if profile else None,
            'languages': profile.get('languages') if profile else None,
            'nationality': profile.get('nationality') if profile else None,
            'interests': profile.get('interests') if profile else None,
            'follower_count': format_follower_count(profile.get('follower_count', 0)) if profile else 0,
        }
    })

@login_required(login_url='/login/')
def user_info_session(request):
    """Returns the connected user's info using session authentication"""
    user = request.user
    
    # Fetch MongoDB profile
    db = get_db()
    profile = db.profiles.find_one({'user_id': user.id})
    
    return JsonResponse({
        'success': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile_image': profile.get('profile_image') if profile else None,
            'date_of_birth': profile.get('date_of_birth') if profile else None,
            'is_staff': user.is_staff,
            'travel_type': profile.get('travel_type') if profile else None,
            'travel_budget': profile.get('travel_budget') if profile else None,
            'gender': profile.get('gender') if profile else None,
            'languages': profile.get('languages') if profile else None,
            'nationality': profile.get('nationality') if profile else None,
            'interests': profile.get('interests') if profile else None,
            'follower_count': format_follower_count(profile.get('follower_count', 0)) if profile else 0,
        }
    })

@csrf_exempt
def login_page(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=email, password=password)
        
        if user:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            # Ensure a profile exists and has a slug for clean URLs
            try:
                profile = user.profile
            except Exception:
                from .models import UserProfile
                profile = UserProfile.objects.create(user=user)
            if not getattr(profile, 'slug', None):
                # Trigger slug generation in model's save()
                profile.save()
            profile_slug = getattr(profile, 'slug', None)
            
            return JsonResponse({
                'success': True,
                'message': 'Login successful',
                'token': access_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'profile_slug': user.profile.slug,  # Ajout du slug pour redirection
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid email or password'
            }, status=400)

@csrf_exempt
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({
            'success': True,
            'message': 'Logged out successfully'
        })
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def register_page(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        date_of_birth = request.POST.get('date_of_birth', '').strip()
        profile_image = request.FILES.get('profile_image')
        travel_type = request.POST.getlist('travel_type')  # Sélection multiple
        travel_budget = request.POST.get('travel_budget', '').strip()
        gender = request.POST.get('gender', '').strip()
        languages = request.POST.getlist('languages')
        nationality = request.POST.get('nationality', '').strip()
        interests = request.POST.getlist('interests')

        errors = []
        if not first_name or not last_name:
            errors.append('First name and last name are required.')
        if not email:
            errors.append('Email is required.')
        if password1 != password2 or not password1:
            errors.append('Passwords must match and not be empty.')
        if not travel_type:
            errors.append('At least one travel type is required.')
        if not travel_budget:
            errors.append('Travel budget is required.')
        if not gender:
            errors.append('Gender is required.')
        if not languages:
            errors.append('At least one language is required.')
        if not nationality:
            errors.append('Country of origin is required.')
        if not interests:
            errors.append('At least one interest is required.')

        if errors:
            return render(request, 'register.html', {
                'errors': errors,
                'interests_list': INTERESTS,
                'travel_types': TRAVEL_TYPES,
                'languages_list': LANGUAGES,
                'countries_list': COUNTRIES,
                'form': {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'date_of_birth': date_of_birth,
                    'travel_type': travel_type,
                    'travel_budget': travel_budget,
                    'gender': gender,
                    'languages': languages,
                    'nationality': nationality,
                    'interests': interests,
                }
            })

        username = email
        try:
            user = User.objects.create_user(username=email, email=email, password=password1,
                                            first_name=first_name, last_name=last_name)
        except IntegrityError:
            return render(request, 'register.html', {
                'errors': ['A user with that email already exists.'],
                'interests_list': INTERESTS,
                'travel_types': TRAVEL_TYPES,
                'languages_list': LANGUAGES,
                'countries_list': COUNTRIES,
                'form': {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'travel_type': travel_type,
                    'travel_budget': travel_budget,
                    'gender': gender,
                    'languages': languages,
                    'nationality': nationality,
                    'interests': interests,
                }
            })

        # Save profile image to MEDIA_ROOT if provided
        profile_image_path = None
        if profile_image:
            fs = FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)
            name, ext = os.path.splitext(profile_image.name)
            unique_name = f"profiles/{uuid.uuid4().hex}{ext}"
            saved_name = fs.save(unique_name, profile_image)
            profile_image_path = os.path.join(settings.MEDIA_URL, saved_name).replace('\\', '/')

        # Save profile to MongoDB
        db = get_db()
        db.profiles.insert_one({
            'user_id': user.id,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': date_of_birth or None,
            'profile_image': profile_image_path,
            'travel_type': travel_type,
            'travel_budget': travel_budget,
            'gender': gender,
            'languages': languages,
            'nationality': nationality,
            'interests': interests,
            'followers': [],  # Initialize empty followers list
            'following': [],  # Initialize empty following list
            'follower_count': 0  # Initialize follower count
        })

        return redirect('login_page')

    return render(request, 'register.html', {
        'interests_list': INTERESTS,
        'travel_types': TRAVEL_TYPES,
        'languages_list': LANGUAGES,
        'countries_list': COUNTRIES
    })

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_unfollow(request):
    """Handle follow/unfollow actions."""
    db = get_db()
    user = request.user
    target_user_id = request.POST.get('target_user_id')
    
    if not target_user_id:
        return JsonResponse({'success': False, 'message': 'Target user ID is required'}, status=400)
    
    try:
        target_user_id = int(target_user_id)
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Invalid user ID'}, status=400)
    
    if target_user_id == user.id:
        return JsonResponse({'success': False, 'message': 'Cannot follow yourself'}, status=400)
    
    user_profile = db.profiles.find_one({'user_id': user.id})
    target_profile = db.profiles.find_one({'user_id': target_user_id})
    
    if not target_profile:
        return JsonResponse({'success': False, 'message': 'Target user not found'}, status=404)
    
    # Check if already following
    is_following = target_user_id in user_profile.get('following', [])
    
    if is_following:
        # Unfollow
        db.profiles.update_one(
            {'user_id': user.id},
            {'$pull': {'following': target_user_id}}
        )
        db.profiles.update_one(
            {'user_id': target_user_id},
            {'$pull': {'followers': user.id}, '$inc': {'follower_count': -1}}
        )
        action = 'unfollowed'
    else:
        # Follow
        db.profiles.update_one(
            {'user_id': user.id},
            {'$addToSet': {'following': target_user_id}}
        )
        db.profiles.update_one(
            {'user_id': target_user_id},
            {'$addToSet': {'followers': user.id}, '$inc': {'follower_count': 1}}
        )
        action = 'followed'
    
    return JsonResponse({'success': True, 'action': action})

# Timeline pages
@login_required(login_url='/login/')
def timeline(request):
    return render(request, 'timeline.html')

@login_required(login_url='/login/')
def timeline_event(request):
    return render(request, 'timeline-event.html')

@login_required(login_url='/login/')
def timeline_funding(request):
    return render(request, 'timeline-funding.html')

@login_required(login_url='/login/')
def timeline_group(request):
    return render(request, 'timeline-group.html')

@login_required(login_url='/login/')
def timeline_page(request):
    return render(request, 'timeline-page.html')

# Feed
@login_required(login_url='/login/')
def feed(request):
    """
    Vue pour afficher le fil d'actualité (feed).
    Affiche tous les posts publics + posts de l'utilisateur.
    Supporte le filtrage par catégorie d'image.
    """
    # Récupérer le filtre de catégorie depuis les paramètres GET
    category_filter = request.GET.get('category', 'all')
    
    # Récupérer tous les posts publics + posts de l'utilisateur
    posts_query = Post.objects.filter(
        Q(visibility='public') | Q(user=request.user)
    )
    
    # 🔍 Filtrage par catégorie d'image
    if category_filter and category_filter != 'all':
        posts_query = posts_query.filter(image_category=category_filter)
    
    posts = posts_query.select_related('user', 'user__profile').prefetch_related(
        'comments', 'comments__user', 'comments__user__profile', 
        'comments__reactions', 'reactions', 'post_shares'
    ).order_by('-created_at')

    # Stories actives (24h)
    from django.utils import timezone
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(hours=24)
    try:
        active_stories_qs = (
            Story.objects.filter(created_at__gte=cutoff)
            .select_related('user', 'user__profile')
            .order_by('-created_at')
        )
        # Force l'évaluation ici pour attraper l'erreur DB avant le template
        active_stories = list(active_stories_qs)
    except DBOperationalError:
        # Table non migrée encore → éviter de casser le feed
        active_stories = []
    
    # 📊 Compter les posts par catégorie (pour les badges de comptage)
    from django.db.models import Count
    category_counts = Post.objects.filter(
        Q(visibility='public') | Q(user=request.user),
        image_category__isnull=False
    ).values('image_category').annotate(count=Count('id'))
    
    # Transformer en dictionnaire pour faciliter l'accès
    counts_dict = {item['image_category']: item['count'] for item in category_counts}
    
    # Mapping des catégories avec leurs informations
    categories = [
        {'id': 'all', 'name': 'Tous', 'icon': '🌍', 'count': posts_query.count()},
        {'id': 'sea', 'name': 'Mer', 'icon': '🌊', 'count': counts_dict.get('sea', 0)},
        {'id': 'mountain', 'name': 'Montagne', 'icon': '⛰️', 'count': counts_dict.get('mountain', 0)},
        {'id': 'forest', 'name': 'Forêt', 'icon': '🌲', 'count': counts_dict.get('forest', 0)},
        {'id': 'buildings', 'name': 'Ville', 'icon': '🏢', 'count': counts_dict.get('buildings', 0)},
        {'id': 'street', 'name': 'Rue', 'icon': '🛣️', 'count': counts_dict.get('street', 0)},
        {'id': 'glacier', 'name': 'Glacier', 'icon': '❄️', 'count': counts_dict.get('glacier', 0)},
    ]
    
    # Pour chaque post, vérifier si l'utilisateur a déjà réagi
    for post in posts:
        # Est-ce que l'utilisateur a liké ce post ?
        post.user_reaction = post.reactions.filter(user=request.user).first()
        
        # Calculer les statistiques
        post.total_reactions = post.reactions.count()
        post.total_comments = post.comments.filter(parent=None).count()  # Seulement les commentaires principaux
        
        # Pour chaque commentaire, vérifier si l'utilisateur a réagi
        for comment in post.comments.all():
            comment.user_reaction = comment.reactions.filter(user=request.user).first()
    
    # 🔎 Log vue du feed (une ligne par appel, pas par post)
    try:
        AnalyticsEvent.objects.create(
            event_type='view_feed',
            user=request.user if request.user.is_authenticated else None,
            media_type='mixed',
            success=True
        )
    except Exception:
        pass

    context = {
        'posts': posts,
        'categories': categories,
        'current_category': category_filter,
        'stories': active_stories,
    }
    return render(request, 'feed.html', context)

# Groups pages
@login_required(login_url='/login/')
def groups(request):
    return render(request, 'groups.html')

@login_required(login_url='/login/')
def groups_2(request):
    return render(request, 'groups-2.html')

# Pages
@login_required(login_url='/login/')
def pages(request):
    db = get_db()
    user = request.user
    user_profile = db.profiles.find_one({'user_id': user.id})
    
    # Récupérer tous les profils sauf celui de l'utilisateur actuel
    profiles = list(db.profiles.find({'user_id': {'$ne': user.id}}))
    
    # Calculer les scores de similarité
    suggested_users = []
    for profile in profiles:
        if profile:  # Vérifier que le profil n'est pas None
            score = calculate_similarity(user_profile, profile) if user_profile else 0
            suggested_users.append({
                'user_id': profile['user_id'],
                'first_name': profile['first_name'],
                'last_name': profile['last_name'],
                'profile_image': profile.get('profile_image', '/static/images/avatars/avatar-default.webp'),
                'follower_count': format_follower_count(profile.get('follower_count', 0)),
                'is_following': user_profile and profile['user_id'] in user_profile.get('following', []),
                'score': score
            })
    
    # Trier par score de similarité (décroissant)
    suggested_users.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Filtrer pour n'afficher que les utilisateurs non suivis
    suggested_users = [user for user in suggested_users if not user['is_following']]
    
    return render(request, 'pages.html', {
        'suggested_users': suggested_users,  # Afficher tous les utilisateurs
    })

    
# Messages
@login_required(login_url='/login/')
def messages_view(request):
    return render(request, 'messages.html')

# Events
@login_required(login_url='/login/')
def event(request):
    return render(request, 'event.html')

@login_required(login_url='/login/')
def event_2(request):
    return render(request, 'event-2.html')

# Market/Shopping
@login_required(login_url='/login/')
def market(request):
    return render(request, 'market.html')

@login_required(login_url='/login/')
def product_view_1(request):
    return render(request, 'product-view-1.html')

@login_required(login_url='/login/')
def product_view_2(request):
    return render(request, 'product-view-2.html')

# Video pages
@login_required(login_url='/login/')
def video(request):
    return render(request, 'video.html')

@login_required(login_url='/login/')
def video_watch(request):
    return render(request, 'video-watch.html')

# Blog pages
@login_required(login_url='/login/')
def blog(request):
    return render(request, 'blog.html')

@login_required(login_url='/login/')
def blog_2(request):
    return render(request, 'blog-2.html')

@login_required(login_url='/login/')
def blog_read(request):
    return render(request, 'blog-read.html')

# Games
@login_required(login_url='/login/')
def games(request):
    return render(request, 'games.html')

# Funding
@login_required(login_url='/login/')
def funding(request):
    return render(request, 'funding.html')

# Settings and account
@login_required(login_url='/login/')
def setting(request):
    return render(request, 'setting.html')

@login_required(login_url='/login/')
def upgrade(request):
    return render(request, 'upgrade.html')

# Single page
@login_required(login_url='/login/')
def single(request):
    return render(request, 'single.html')
@login_required(login_url='/login/')
def profile_view(request, slug=None):
    """Affiche le profil d'un utilisateur avec ses posts (via son slug unique)"""
    if slug:
        # Si l'URL contient un email par erreur, rediriger vers le bon slug
        if '@' in slug:
            # Essayer de retrouver l'utilisateur par username/email
            try:
                usr = User.objects.get(username=slug)
            except User.DoesNotExist:
                try:
                    usr = User.objects.get(email=slug)
                except User.DoesNotExist:
                    usr = None
            if usr and hasattr(usr, 'profile') and usr.profile.slug:
                return redirect('profile', slug=usr.profile.slug)
        # Récupérer le profil par son slug, puis l'utilisateur
        profile = UserProfile.objects.select_related('user').get(slug=slug)
        user = profile.user
    else:
        user = request.user
    
    # Récupérer tous les posts de cet utilisateur
    user_posts = Post.objects.filter(user=user).select_related(
        'user', 'user__profile'
    ).prefetch_related(
        'comments', 'comments__user', 'comments__user__profile',
        'comments__reactions', 'reactions', 'post_shares'
    ).order_by('-created_at')
    
    # Pour chaque post, ajouter les infos de réaction de l'utilisateur connecté
    if request.user.is_authenticated:
        for post in user_posts:
            post.user_reaction = post.reactions.filter(user=request.user).first()
            post.total_reactions = post.reactions.count()
            post.total_comments = post.comments.filter(parent=None).count()
            
            # Pour chaque commentaire, vérifier si l'utilisateur a réagi
            for comment in post.comments.all():
                comment.user_reaction = comment.reactions.filter(user=request.user).first()
    
    # Avis stats for profile badge
    avis_qs = Avis.objects.filter(reviewee=user)
    stats = avis_qs.aggregate(
        avg_note=Avg('note'),
        avg_comm=Avg('communication'),
        avg_fiab=Avg('fiabilite'),
        avg_symp=Avg('sympathie'),
        reviews_count=Count('id')
    )
    context = {
        'user': user,
        'profile': user.profile,
        'user_posts': user_posts,
        'posts_count': user_posts.count(),
        'avg_review_note': round(stats['avg_note'] or 0, 2),
        'reviews_count': stats['reviews_count'] or 0,
    }
    return render(request, 'profile.html', context)


@login_required(login_url='/login/')
def profile_albums(request, slug):
    """Affiche les albums automatiques d'un utilisateur, groupés par image_category."""
    # Identifier l'utilisateur par son slug
    profile = UserProfile.objects.select_related('user').get(slug=slug)
    user = profile.user

    # Filtre actif
    category_filter = request.GET.get('category', 'all')

    # Base queryset: uniquement les posts avec image et catégorie connue
    # Attention: certains FileField peuvent être non nuls mais vides -> exclure image=""
    base_qs = Post.objects.filter(user=user, image__isnull=False).exclude(image="")

    # Comptages par catégorie pour les badges
    counts = base_qs.exclude(image_category__isnull=True).values('image_category').annotate(count=Count('id'))
    counts_dict = {row['image_category']: row['count'] for row in counts}

    categories = [
        {'id': 'all', 'name': 'Tous', 'icon': '🌍', 'count': base_qs.count()},
        {'id': 'sea', 'name': 'Mer', 'icon': '🌊', 'count': counts_dict.get('sea', 0)},
        {'id': 'mountain', 'name': 'Montagne', 'icon': '⛰️', 'count': counts_dict.get('mountain', 0)},
        {'id': 'forest', 'name': 'Forêt', 'icon': '🌲', 'count': counts_dict.get('forest', 0)},
        {'id': 'buildings', 'name': 'Ville', 'icon': '🏢', 'count': counts_dict.get('buildings', 0)},
        {'id': 'street', 'name': 'Rue', 'icon': '🛣️', 'count': counts_dict.get('street', 0)},
        {'id': 'glacier', 'name': 'Glacier', 'icon': '❄️', 'count': counts_dict.get('glacier', 0)},
    ]

    # Appliquer le filtre si choisi
    images_qs = base_qs
    if category_filter != 'all':
        images_qs = images_qs.filter(image_category=category_filter)

    images_qs = images_qs.only('id', 'image', 'image_category').order_by('-created_at')

    # Pagination
    paginator = Paginator(images_qs, 24)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'profile_user': user,
        'profile': profile,
        'categories': categories,
        'current_category': category_filter,
        'page_obj': page_obj,
        'images': page_obj.object_list,
    }
    return render(request, 'profile_albums.html', context)


@login_required(login_url='/login/')
def profile_analytics(request, slug):
    """
    Tableau de bord analytique IA pour un utilisateur (dans son profil).
    Montre ses stats: types de médias, catégories d'images, langues détectées,
    et engagement (likes, commentaires, partages).
    """
    profile = UserProfile.objects.select_related('user').get(slug=slug)
    user = profile.user

    # Posts de l'utilisateur
    user_posts = Post.objects.filter(user=user)

    # KPIs
    total_posts = user_posts.count()
    total_images = user_posts.filter(image__isnull=False).exclude(image="").count()
    total_videos = user_posts.filter(video__isnull=False).exclude(video="").count()
    total_voice = user_posts.filter(voice_note__isnull=False).exclude(voice_note="").count()

    # Engagement
    total_likes = user_posts.aggregate(c=Count('reactions'))['c'] or 0
    total_comments = user_posts.aggregate(c=Count('comments'))['c'] or 0
    total_shares = user_posts.aggregate(c=Count('post_shares'))['c'] or 0

    # Répartition catégories et langues
    cat_counts = (
        user_posts.exclude(image_category__isnull=True)
        .values('image_category')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    lang_counts = (
        user_posts.exclude(detected_language__isnull=True)
        .values('detected_language')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    context = {
        'profile_user': user,
        'profile': profile,
        'kpis': {
            'total_posts': total_posts,
            'total_images': total_images,
            'total_videos': total_videos,
            'total_voice': total_voice,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_shares': total_shares,
        },
        'category_counts': list(cat_counts),
        'lang_counts': list(lang_counts),
    }
    return render(request, 'profile_analytics.html', context)
def get_country_flag(country_code):
    """Convertir un code pays (ex: 'FR') en emoji drapeau (ex: '🇫🇷')"""
    OFFSET = 127397
    return ''.join(chr(ord(char) + OFFSET) for char in country_code)

@login_required
def edit_profile(request):
    """Édite le profil de l'utilisateur connecté"""
    db = get_db()
    mongo_profile = db.profiles.find_one({'user_id': request.user.id})
    
    # Initialiser visited_countries si elle n'existe pas
    if mongo_profile is None:
        mongo_profile = {}
    if 'visited_countries' not in mongo_profile:
        mongo_profile['visited_countries'] = []
    
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(
            request.POST, 
            request.FILES,
            instance=request.user.profile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                user_form.save()
                profile_form.save()
                
                # Mettre à jour les données MongoDB (avec upsert pour créer si n'existe pas)
                mongo_updates = {
                    'user_id': request.user.id,  # Ajout de l'user_id pour la création
                    'email': request.user.email,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'travel_type': request.POST.getlist('travel_type'),
                    'travel_budget': request.POST.get('travel_budget', ''),
                    'gender': request.POST.get('gender', ''),
                    'languages': request.POST.getlist('languages'),
                    'nationality': request.POST.get('nationality', ''),
                    'interests': request.POST.getlist('interests'),
                    'visited_countries': request.POST.getlist('visited_countries'),
                }
                
                # upsert=True : crée le document s'il n'existe pas, sinon le met à jour
                db.profiles.update_one(
                    {'user_id': request.user.id},
                    {'$set': mongo_updates},
                    upsert=True
                )
                
                messages.success(request, '✅ Votre profil a été mis à jour avec succès ! Toutes vos modifications ont été enregistrées.')
                return redirect('profile', slug=request.user.profile.slug)
            except Exception as e:
                messages.error(request, f'❌ Une erreur est survenue lors de la sauvegarde : {str(e)}')
        else:
            if user_form.errors or profile_form.errors:
                error_messages = []
                for field, errors in user_form.errors.items():
                    for error in errors:
                        error_messages.append(f'{user_form.fields[field].label}: {error}')
                for field, errors in profile_form.errors.items():
                    for error in errors:
                        error_messages.append(f'{profile_form.fields[field].label}: {error}')
                if error_messages:
                    messages.error(request, '❌ Veuillez corriger les erreurs suivantes :')
                    for error_msg in error_messages[:3]:
                        messages.error(request, f'  • {error_msg}')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
    
    # Transformer la liste de pays en liste de dictionnaires avec drapeaux
    countries_with_flags = [
        {
            'code': code,
            'name': name,
            'flag': get_country_flag(code)
        }
        for code, name in COUNTRIES
    ]
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'mongo_profile': mongo_profile or {},
        'interests_list': INTERESTS,
        'travel_types': TRAVEL_TYPES,
        'languages_list': LANGUAGES,
        'countries_list': countries_with_flags,
    }
    return render(request, 'edit_profile.html', context)

@login_required
def change_password(request):
    """Change le mot de passe de l'utilisateur connecté"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Importante : garder l'utilisateur connecté après le changement de mot de passe
            update_session_auth_hash(request, user)
            messages.success(request, '🔒 Votre mot de passe a été modifié avec succès !')
            return redirect('edit_profile')
        else:
            for error in form.non_field_errors():
                messages.error(request, f'❌ {error}')
            for field, errors in form.errors.items():
                if field != '__all__':
                    for error in errors:
                        messages.error(request, f'❌ {form.fields[field].label}: {error}')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    
    return render(request, 'change_password.html', {'form': form})

# ============================================
# REVIEWS
# ============================================
@login_required(login_url='/login/')
def reviews_list(request, slug):
    # target user by slug
    target_profile = UserProfile.objects.select_related('user').get(slug=slug)
    target_user = target_profile.user
    # Ensure profile has a slug
    if not target_profile.slug:
        target_profile.save()

    qs = Avis.objects.filter(reviewee=target_user)

    # filters
    def clamp_int(param):
        try:
            v = int(request.GET.get(param, 0))
            return min(5, max(0, v))
        except (TypeError, ValueError):
            return 0
    min_note = clamp_int('min_note')
    min_comm = clamp_int('min_comm')
    min_fiab = clamp_int('min_fiab')
    min_symp = clamp_int('min_symp')
    if min_note:
        qs = qs.filter(note__gte=min_note)
    if min_comm:
        qs = qs.filter(communication__gte=min_comm)
    if min_fiab:
        qs = qs.filter(fiabilite__gte=min_fiab)
    if min_symp:
        qs = qs.filter(sympathie__gte=min_symp)

    # sort
    sort = request.GET.get('sort', 'recent')
    order_map = {
        'recent': '-created_at',
        'oldest': 'created_at',
        'note_desc': '-note',
        'note_asc': 'note',
        'comm_desc': '-communication',
        'fiab_desc': '-fiabilite',
        'symp_desc': '-sympathie',
    }
    qs = qs.order_by(order_map.get(sort, '-created_at'))

    # stats
    stats = Avis.objects.filter(reviewee=target_user).aggregate(
        avg_note=Avg('note'),
        avg_comm=Avg('communication'),
        avg_fiab=Avg('fiabilite'),
        avg_symp=Avg('sympathie'),
        reviews_count=Count('id')
    )
    def pct(v):
        return int(round(((v or 0) / 5) * 100))

    # pagination
    from django.core.paginator import Paginator
    paginator = Paginator(qs, 6)
    page_obj = paginator.get_page(request.GET.get('page'))

    # flags: can_review and existing_by_me
    existing_by_me = None
    can_review = False
    if request.user.is_authenticated and request.user != target_user:
        existing_by_me = Avis.objects.filter(reviewer=request.user, reviewee=target_user).first()
        # mutual follow check via mongo
        try:
            db = get_db()
            me = db.profiles.find_one({'user_id': request.user.id}) or {}
            him = db.profiles.find_one({'user_id': target_user.id}) or {}
            can_review = (
                (target_user.id in (me.get('following', []))) and
                (request.user.id in (him.get('following', []))) and
                (existing_by_me is None)
            )
        except Exception:
            can_review = False

    context = {
        'target_user': target_user,
        'target_profile': target_profile,
        'profile': target_profile,
        'slug': target_profile.slug,
        'page_obj': page_obj,
        'avis_page': page_obj,
        'sort': sort,
        'min_note': min_note,
        'min_comm': min_comm,
        'min_fiab': min_fiab,
        'min_symp': min_symp,
        'avg_note': round(stats['avg_note'] or 0, 2),
        'avg_comm': round(stats['avg_comm'] or 0, 2),
        'avg_fiab': round(stats['avg_fiab'] or 0, 2),
        'avg_symp': round(stats['avg_symp'] or 0, 2),
        'avg_note_pct': pct(stats['avg_note']),
        'avg_comm_pct': pct(stats['avg_comm']),
        'avg_fiab_pct': pct(stats['avg_fiab']),
        'avg_symp_pct': pct(stats['avg_symp']),
        'reviews_count': stats['reviews_count'] or 0,
        'avis_count': stats['reviews_count'] or 0,
        'can_review': can_review,
        'existing_by_me': existing_by_me,
    }
    return render(request, 'reviews/list.html', context)

@login_required(login_url='/login/')
def review_create(request, slug):
    target_profile = UserProfile.objects.select_related('user').get(slug=slug)
    target_user = target_profile.user
    if not target_profile.slug:
        target_profile.save()
    if request.method == 'POST':
        try:
            note = int(request.POST.get('note'))
            communication = int(request.POST.get('communication'))
            fiabilite = int(request.POST.get('fiabilite'))
            sympathie = int(request.POST.get('sympathie'))
        except (TypeError, ValueError):
            messages.error(request, 'Notes invalides.')
            return redirect('review_create', slug=slug)
        commentaire = request.POST.get('commentaire', '').strip()

        avis = Avis(
            reviewer=request.user,
            reviewee=target_user,
            note=note,
            communication=communication,
            fiabilite=fiabilite,
            sympathie=sympathie,
            commentaire=commentaire or None,
        )
        try:
            avis.save()
            messages.success(request, 'Votre avis a été enregistré.')
            return redirect('reviews_list', slug=slug)
        except Exception as e:
            messages.error(request, str(e))
            return redirect('review_create', slug=slug)

    return render(request, 'reviews/create.html', {
        'target_user': target_user,
        'target_profile': target_profile,
        'profile': target_profile,
        'slug': target_profile.slug,
    })
    # ============================================
# VUE : CRÉER UN POST
# ============================================
@login_required
def create_post(request):
    """
    Vue pour créer un nouveau post avec vérification des quotas.
    Supporte : texte, image, vidéo, note vocale, localisation
    """
    if request.method == 'POST':
        # ✅ VÉRIFIER LES QUOTAS AVANT DE CRÉER LE POST
        can_post, error_msg = can_user_perform_action(request.user, 'post')
        if not can_post:
            return JsonResponse({
                'success': False,
                'error': error_msg,
                'upgrade_url': '/upgrade/'
            }, status=403)
        
        # Récupérer les données du formulaire
        content = request.POST.get('content', '').strip()
        location = request.POST.get('location', '').strip()
        visibility = request.POST.get('visibility', 'public')
        
        # Récupérer les fichiers uploadés
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        voice_note = request.FILES.get('voice_note')
        
        # Validation : Au moins un contenu doit être présent
        if not content and not image and not video and not voice_note:
            return JsonResponse({
                'success': False,
                'error': 'Veuillez ajouter du contenu, une image, une vidéo ou une note vocale.'
            }, status=400)
        
        # Créer le post
        post = Post.objects.create(
            user=request.user,
            content=content,
            image=image,
            video=video,
            voice_note=voice_note,
            location=location,
            visibility=visibility
        )
        
        # ✅ INCRÉMENTER LE COMPTEUR DE QUOTAS
        increment_usage(request.user, 'post')
        
        # Retourner une réponse JSON (succès)
        return JsonResponse({
            'success': True,
            'message': 'Post créé avec succès !',
            'post_id': post.id
        })
    
    # Si GET : afficher le formulaire de création
    return render(request, 'create_post.html')
    """
    Vue pour créer un nouveau post.
    Supporte : texte, image, vidéo, note vocale, localisation
    """
    if request.method == 'POST':
        # Récupérer les données du formulaire
        content = request.POST.get('content', '').strip()
        location = request.POST.get('location', '').strip()
        visibility = request.POST.get('visibility', 'public')
        
        # Récupérer les fichiers uploadés
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        voice_note = request.FILES.get('voice_note')
        
        # Validation : Au moins un contenu doit être présent
        if not content and not image and not video and not voice_note:
            return JsonResponse({
                'success': False,
                'error': 'Veuillez ajouter du contenu, une image, une vidéo ou une note vocale.'
            }, status=400)
        
        # Créer le post
        post = Post.objects.create(
            user=request.user,
            content=content,
            image=image,
            video=video,
            voice_note=voice_note,
            location=location,
            visibility=visibility
        )
        
        # ✅ IA : Transcription automatique avec Whisper (notes vocales ET vidéos)
        transcription_success = False
        media_to_transcribe = None
        media_type = None
        
        # Déterminer quel média doit être transcrit
        if voice_note:
            media_to_transcribe = post.voice_note
            media_type = "note vocale"
        elif video:
            media_to_transcribe = post.video
            media_type = "vidéo"
        
        # Lancer la transcription si un média audio/vidéo est présent
        if media_to_transcribe:
            print(f"🎤 [IA] Lancement de la transcription Whisper ({media_type})...")
            result = transcribe_voice_note(media_to_transcribe)
            
            if result['success']:
                # Sauvegarder la transcription dans le post
                post.voice_transcription = result['text']
                post.detected_language = result['language']
                post.save()
                transcription_success = True
                print(f"✅ [IA] Transcription sauvegardée : {result['language_name']} ({result['language']})")
            else:
                print(f"❌ [IA] Erreur de transcription : {result.get('error', 'Erreur inconnue')}")
        
        # ✅ IA : Classification automatique d'images de voyage (ResNet18)
        classification_success = False
        if image:
            print(f"🖼️ [IA] Lancement de la classification d'image...")
            classification_result = classify_travel_image(post.image)
            
            if classification_result['success']:
                # Sauvegarder la classification dans le post
                post.image_category = classification_result['category']
                post.image_category_fr = classification_result['category_fr']
                post.image_confidence = classification_result['confidence']
                
                # Générer les tags automatiques
                post.image_tags = get_image_tags(post.image)
                
                post.save()
                classification_success = True
                print(f"✅ [IA] Image classifiée : {classification_result['category_fr']} ({classification_result['confidence']*100:.1f}%)")
                print(f"   Tags générés : {', '.join(post.image_tags)}")
            else:
                print(f"❌ [IA] Erreur de classification : {classification_result.get('error', 'Erreur inconnue')}")
        
        # 📊 Analytics: log création + résultats IA
        try:
            media_type = 'text'
            if image and video:
                media_type = 'mixed'
            elif image:
                media_type = 'image'
            elif video:
                media_type = 'video'
            elif voice_note:
                media_type = 'voice'

            # create_post event
            AnalyticsEvent.objects.create(
                event_type='create_post',
                user=request.user,
                post=post,
                media_type=media_type,
                image_category=post.image_category,
                detected_language=post.detected_language,
                success=True,
                meta={
                    'has_transcription': transcription_success,
                    'has_classification': classification_success,
                }
            )

            # whisper result
            if media_to_transcribe is not None:
                AnalyticsEvent.objects.create(
                    event_type='whisper_ok' if transcription_success else 'whisper_fail',
                    user=request.user,
                    post=post,
                    media_type='voice' if voice_note else 'video',
                    detected_language=post.detected_language,
                    success=transcription_success
                )

            # classify result
            if image is not None:
                AnalyticsEvent.objects.create(
                    event_type='classify_ok' if classification_success else 'classify_fail',
                    user=request.user,
                    post=post,
                    media_type='image',
                    image_category=post.image_category,
                    success=classification_success,
                    meta={'confidence': post.image_confidence}
                )
        except Exception:
            pass

        # Retourner une réponse JSON (succès)
        return JsonResponse({
            'success': True,
            'message': 'Post créé avec succès !',
            'post_id': post.id,
            'has_transcription': transcription_success,
            'transcription': post.voice_transcription if transcription_success else None,
            'has_classification': classification_success,
            'image_category': post.image_category_fr if classification_success else None,
            'image_confidence': post.image_confidence if classification_success else None,
            'image_tags': post.image_tags if classification_success else None
        })
    
    # Si GET : afficher le formulaire de création
    return render(request, 'create_post.html')


# ============================================
# API : ANALYSER UNE IMAGE POUR GÉNÉRER DES TAGS
# ============================================
@csrf_exempt
@login_required(login_url='/login/')
def analyze_image_for_tags(request):
    """
    API pour analyser une image et retourner des tags automatiques
    AVANT la création du post.
    
    Utilisé par JavaScript en temps réel quand l'utilisateur sélectionne une image.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    if 'image' not in request.FILES:
        return JsonResponse({'error': 'Aucune image fournie'}, status=400)
    
    try:
        # Récupérer l'image uploadée
        image = request.FILES['image']
        
        print(f"📥 [API] Réception d'une image pour analyse : {image.name}")
        
        # Sauvegarder temporairement l'image
        import tempfile
        import os
        
        # Créer un fichier temporaire avec la bonne extension
        file_extension = os.path.splitext(image.name)[1] or '.jpg'
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            for chunk in image.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name
        
        print(f"💾 [API] Image sauvegardée temporairement : {temp_path}")
        
        # Importer les fonctions d'analyse
        from .ai_services import classify_travel_image_from_path, get_image_tags_from_classification
        
        # Analyser l'image avec l'IA
        classification = classify_travel_image_from_path(temp_path)
        
        # Nettoyer le fichier temporaire
        try:
            os.unlink(temp_path)
            print(f"🗑️ [API] Fichier temporaire supprimé")
        except Exception as e:
            print(f"⚠️ [API] Impossible de supprimer le fichier temporaire : {e}")
        
        # Vérifier si la classification a réussi
        if not classification.get('success'):
            return JsonResponse({
                'success': False,
                'error': classification.get('error', 'Erreur d\'analyse')
            }, status=500)
        
        # Générer les tags basés sur la classification
        tags = get_image_tags_from_classification(classification)
        
        print(f"✅ [API] Tags générés : {', '.join(tags)}")
        
        # Retourner les résultats
        return JsonResponse({
            'success': True,
            'category': classification.get('category_fr', ''),
            'confidence': round(classification.get('confidence', 0) * 100, 1),  # Convertir en %
            'tags': tags
        })
    
    except Exception as e:
        print(f"❌ [API] Erreur : {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


    # ============================================
# VUE : AFFICHER LE FIL D'ACTUALITÉ
# ============================================
@login_required(login_url='/login/')

def list_posts(request):
    """
    Vue pour afficher le fil d'actualité (feed).
    Affiche tous les posts publics + posts d'amis.
    """
    # Récupérer tous les posts publics (on peut filtrer par amis plus tard)
    posts = Post.objects.filter(
        Q(visibility='public') | Q(user=request.user)
    ).select_related('user', 'user__profile').prefetch_related(
        'comments', 'reactions', 'post_shares'
    ).order_by('-created_at')
    
    # Pour chaque post, vérifier si l'utilisateur a déjà réagi
    for post in posts:
        # Est-ce que l'utilisateur a liké ce post ?
        post.user_reaction = post.reactions.filter(user=request.user).first()
        
        # Calculer les statistiques
        post.total_reactions = post.reactions.count()
        post.total_comments = post.comments.filter(parent=None).count()  # Seulement les commentaires principaux
    
    context = {
        'posts': posts,
    }
    return render(request, 'feed.html', context)


# ============================================
# DASHBOARD ANALYTIQUE IA
# ============================================
@login_required(login_url='/login/')
def analytics_dashboard(request):
    """
    Page tableau de bord analytique IA (graphiques + métriques clés).
    """
    # KPIs rapides (synchro)
    total_posts = Post.objects.count()
    total_images = Post.objects.filter(image__isnull=False).exclude(image="").count()
    total_videos = Post.objects.filter(video__isnull=False).exclude(video="").count()
    total_voice = Post.objects.filter(voice_note__isnull=False).exclude(voice_note="").count()

    whisper_ok = AnalyticsEvent.objects.filter(event_type='whisper_ok').count()
    whisper_fail = AnalyticsEvent.objects.filter(event_type='whisper_fail').count()
    classify_ok = AnalyticsEvent.objects.filter(event_type='classify_ok').count()
    classify_fail = AnalyticsEvent.objects.filter(event_type='classify_fail').count()

    # Répartition par catégories IA (top)
    category_counts = (
        Post.objects.exclude(image_category__isnull=True)
        .values('image_category')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Répartition par langues détectées (top)
    lang_counts = (
        Post.objects.exclude(detected_language__isnull=True)
        .values('detected_language')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    context = {
        'kpis': {
            'total_posts': total_posts,
            'total_images': total_images,
            'total_videos': total_videos,
            'total_voice': total_voice,
            'whisper_ok': whisper_ok,
            'whisper_fail': whisper_fail,
            'classify_ok': classify_ok,
            'classify_fail': classify_fail,
        },
        'category_counts': list(category_counts),
        'lang_counts': list(lang_counts),
    }
    return render(request, 'analytics_dashboard.html', context)


@login_required(login_url='/login/')
def analytics_data(request):
    """
    API JSON pour alimenter Chart.js (données dynamiques).
    """
    # séries temporelles simples (7 derniers jours)
    from django.utils import timezone
    from datetime import timedelta

    today = timezone.now().date()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]

    def count_on(day, qs):
        start = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time()))
        end = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.max.time()))
        return qs.filter(created_at__gte=start, created_at__lte=end).count()

    events = AnalyticsEvent.objects.all()
    create_counts = [count_on(d, events.filter(event_type='create_post')) for d in days]
    whisper_ok_counts = [count_on(d, events.filter(event_type='whisper_ok')) for d in days]
    classify_ok_counts = [count_on(d, events.filter(event_type='classify_ok')) for d in days]

    # Répartition courante par catégories et langues
    cat = (
        Post.objects.exclude(image_category__isnull=True)
        .values('image_category')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    lang = (
        Post.objects.exclude(detected_language__isnull=True)
        .values('detected_language')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    return JsonResponse({
        'success': True,
        'series': {
            'days': [d.strftime('%d/%m') for d in days],
            'create_posts': create_counts,
            'whisper_ok': whisper_ok_counts,
            'classify_ok': classify_ok_counts,
        },
        'categories': list(cat),
        'languages': list(lang),
    })


# ============================================
# STORIES
# ============================================
@login_required(login_url='/login/')
@require_http_methods(["POST"])
def create_story(request):
    """Créer une story (texte/image/vidéo) valable 24h."""
    content_text = request.POST.get('content_text', '').strip() or None
    image = request.FILES.get('image')
    video = request.FILES.get('video')

    if not content_text and not image and not video:
        return JsonResponse({'success': False, 'error': 'Ajoutez un texte, une image ou une vidéo.'}, status=400)

    story = Story.objects.create(user=request.user, content_text=content_text, image=image, video=video)
    return JsonResponse({'success': True, 'story_id': story.id})


@login_required(login_url='/login/')
def list_stories(request):
    """Lister les stories actives (24h) pour affichage léger."""
    from django.utils import timezone
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(hours=24)
    stories = Story.objects.filter(created_at__gte=cutoff).select_related('user', 'user__profile').order_by('-created_at')
    data = []
    for s in stories:
        data.append({
            'id': s.id,
            'user': {
                'id': s.user.id,
                'name': f"{s.user.first_name} {s.user.last_name}".strip() or s.user.username,
                'avatar': s.user.profile.avatar.url if s.user.profile.avatar else None,
            },
            'content_text': s.content_text,
            'image': s.image.url if s.image else None,
            'video': s.video.url if s.video else None,
            'created_at': s.created_at.strftime('%d/%m/%Y %H:%M')
        })
    return JsonResponse({'success': True, 'stories': data})


@login_required(login_url='/login/')
def story_detail(request, story_id):
    """Retourne le contenu d'une story et enregistre la vue."""
    from django.utils import timezone
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(hours=24)
    try:
        story = Story.objects.select_related('user', 'user__profile').get(id=story_id, created_at__gte=cutoff)
    except Story.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Story expirée ou introuvable'}, status=404)

    # Enregistrer la vue (sauf pour l'auteur)
    if request.user != story.user:
        StoryView.objects.get_or_create(story=story, viewer=request.user)

    return JsonResponse({
        'success': True,
        'story': {
            'id': story.id,
            'user': {
                'id': story.user.id,
                'name': f"{story.user.first_name} {story.user.last_name}".strip() or story.user.username,
                'avatar': story.user.profile.avatar.url if story.user.profile.avatar else None,
            },
            'content_text': story.content_text,
            'image': story.image.url if story.image else None,
            'video': story.video.url if story.video else None,
            'created_at': story.created_at.strftime('%d/%m/%Y %H:%M'),
            'expires_at': (story.created_at + timezone.timedelta(hours=24)).strftime('%d/%m/%Y %H:%M'),
            'views_count': story.views.count()
        }
    })
# ============================================
# VUE : SUPPRIMER UN POST
# ============================================
@login_required(login_url='/login/')
@require_http_methods(["POST", "DELETE"])
def delete_post(request, post_id):
    """
    Vue pour supprimer un post.
    Seul le créateur du post peut le supprimer.
    """
    # Récupérer le post (ou 404 si n'existe pas)
    post = get_object_or_404(Post, id=post_id)
    
    # Vérifier que l'utilisateur est bien le créateur du post
    if post.user != request.user:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'avez pas la permission de supprimer ce post.'
        }, status=403)
    
    # Supprimer le post
    post.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Post supprimé avec succès !'
    })

# ============================================
# VUE : MODIFIER UN POST
# ============================================
@login_required(login_url='/login/')
@require_http_methods(["POST"])
def edit_post(request, post_id):
    """
    Vue pour modifier le contenu d'un post.
    Seul le créateur du post peut le modifier.
    """
    # Récupérer le post (ou 404 si n'existe pas)
    post = get_object_or_404(Post, id=post_id)
    
    # Vérifier que l'utilisateur est bien le créateur du post
    if post.user != request.user:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'avez pas la permission de modifier ce post.'
        }, status=403)
    
    # Récupérer le nouveau contenu
    new_content = request.POST.get('content', '').strip()
    
    # Vérifier que le contenu n'est pas vide
    if not new_content:
        return JsonResponse({
            'success': False,
            'error': 'Le post ne peut pas être vide.'
        }, status=400)
    
    # Mettre à jour le contenu du post
    post.content = new_content
    post.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Post modifié avec succès !',
        'post': {
            'id': post.id,
            'content': post.content,
            'updated_at': post.updated_at.strftime('%d/%m/%Y %H:%M')
        }
    })

# ============================================
# VUE : AJOUTER UN COMMENTAIRE
# ============================================
@login_required(login_url='/login/')
@require_http_methods(["POST"])
def add_comment(request, post_id):
    """
    Vue pour ajouter un commentaire sur un post.
    Supporte : texte, image, emojis, commentaires imbriqués (réponses).
    """
    # Récupérer le post
    post = get_object_or_404(Post, id=post_id)
    
    # Récupérer les données
    content = request.POST.get('content', '').strip()
    parent_id = request.POST.get('parent_id')  # Si c'est une réponse à un autre commentaire
    image = request.FILES.get('image')
    
    # Validation : Au moins du contenu OU une image
    if not content and not image:
        return JsonResponse({
            'success': False,
            'error': 'Le commentaire doit contenir du texte ou une image.'
        }, status=400)
    
    # Créer le commentaire
    comment = Comment.objects.create(
        post=post,
        user=request.user,
        content=content,
        image=image,
        parent_id=parent_id if parent_id else None
    )
    
    # Incrémenter le compteur de commentaires du post
    post.comments_count += 1
    post.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Commentaire ajouté avec succès !',
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'image': comment.image.url if comment.image else None,
            'user': comment.user.username,
            'user_avatar': comment.user.profile.avatar.url if comment.user.profile.avatar else None,
            'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M')
        }
    })
    # ============================================
# VUE : AJOUTER/MODIFIER UNE RÉACTION
# ============================================
@login_required(login_url='/login/')
@require_http_methods(["POST"])
def add_reaction(request, post_id):
    """
    Vue pour ajouter ou modifier une réaction sur un post.
    Si l'utilisateur a déjà réagi, on met à jour sa réaction.
    Si c'est la même réaction, on la supprime (toggle).
    """
    # Récupérer le post
    post = get_object_or_404(Post, id=post_id)
    
    # Récupérer le type de réaction (like, love, haha, wow, sad, angry)
    reaction_type = request.POST.get('reaction_type', 'like')
    
    # Vérifier si l'utilisateur a déjà réagi à ce post
    existing_reaction = Reaction.objects.filter(user=request.user, post=post).first()
    
    if existing_reaction:
        # Si c'est la même réaction → SUPPRIMER (toggle off)
        if existing_reaction.reaction_type == reaction_type:
            existing_reaction.delete()
            
            # Décrémenter le compteur
            post.likes_count = max(0, post.likes_count - 1)
            post.save()
            
            return JsonResponse({
                'success': True,
                'action': 'removed',
                'message': 'Réaction supprimée',
                'likes_count': post.likes_count
            })
        else:
            # Si c'est une réaction différente → MODIFIER
            existing_reaction.reaction_type = reaction_type
            existing_reaction.save()
            
            return JsonResponse({
                'success': True,
                'action': 'updated',
                'message': 'Réaction modifiée',
                'reaction_type': reaction_type,
                'likes_count': post.likes_count
            })
    else:
        # Créer une nouvelle réaction
        Reaction.objects.create(
            user=request.user,
            post=post,
            reaction_type=reaction_type
        )
        
        # Incrémenter le compteur
        post.likes_count += 1
        post.save()
        
        return JsonResponse({
            'success': True,
            'action': 'added',
            'message': 'Réaction ajoutée',
            'reaction_type': reaction_type,
            'likes_count': post.likes_count
        })
        # ============================================
# VUE : RÉAGIR À UN COMMENTAIRE
# ============================================
@login_required(login_url='/login/')
@require_http_methods(["POST"])
def react_to_comment(request, comment_id):
    """
    Vue pour ajouter/supprimer une réaction sur un commentaire.
    Fonctionne comme la réaction sur un post.
    """
    # Récupérer le commentaire
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Récupérer le type de réaction
    reaction_type = request.POST.get('reaction_type', 'like')
    
    # Vérifier si l'utilisateur a déjà réagi
    existing_reaction = Reaction.objects.filter(user=request.user, comment=comment).first()
    
    if existing_reaction:
        # Toggle : supprimer si même réaction
        if existing_reaction.reaction_type == reaction_type:
            existing_reaction.delete()
            comment.likes_count = max(0, comment.likes_count - 1)
            comment.save()
            
            return JsonResponse({
                'success': True,
                'action': 'removed',
                'likes_count': comment.likes_count
            })
        else:
            # Modifier la réaction
            existing_reaction.reaction_type = reaction_type
            existing_reaction.save()
            
            return JsonResponse({
                'success': True,
                'action': 'updated',
                'reaction_type': reaction_type,
                'likes_count': comment.likes_count
            })
    else:
        # Créer une nouvelle réaction
        Reaction.objects.create(
            user=request.user,
            comment=comment,
            reaction_type=reaction_type
        )
        
        comment.likes_count += 1
        comment.save()
        
        return JsonResponse({
            'success': True,
            'action': 'added',
            'reaction_type': reaction_type,
            'likes_count': comment.likes_count
        })
        # ============================================
# VUE : PARTAGER UN POST
# ============================================
@login_required(login_url='/login/')
@require_http_methods(["POST"])
def share_post(request, post_id):
    """
    Vue pour partager un post.
    Crée un nouveau post qui référence le post original.
    """
    # Récupérer le post original
    original_post = get_object_or_404(Post, id=post_id)
    
    # Récupérer le message optionnel
    message = request.POST.get('message', '').strip()
    
    # Vérifier que l'utilisateur ne partage pas son propre post
    # (optionnel : vous pouvez autoriser cela si vous voulez)
    if original_post.user == request.user:
        return JsonResponse({
            'success': False,
            'error': 'Vous ne pouvez pas partager votre propre post.'
        }, status=400)
    
    # Créer un enregistrement de partage
    share = Share.objects.create(
        user=request.user,
        original_post=original_post,
        message=message
    )
    
    # Créer un nouveau post qui référence le post partagé
    shared_post = Post.objects.create(
        user=request.user,
        content=message,
        shared_post=original_post,
        visibility='public'  # Ou selon vos besoins
    )
    
    # Incrémenter le compteur de partages
    original_post.shares_count += 1
    original_post.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Post partagé avec succès !',
        'share_id': share.id,
        'shared_post_id': shared_post.id,
        'shares_count': original_post.shares_count
    })
    # ============================================
# VUE : OBTENIR LES DÉTAILS D'UN POST (API)
# ============================================
@login_required(login_url='/login/')
def get_post_detail(request, post_id):
    """
    Vue API pour récupérer les détails d'un post avec tous ses commentaires et réactions.
    Utile pour l'affichage modal ou la page de détail.
    """
    # Récupérer le post
    post = get_object_or_404(Post, id=post_id)
    
    # Vérifier la visibilité
    if post.visibility == 'private' and post.user != request.user:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'avez pas accès à ce post.'
        }, status=403)
    
    # Récupérer les commentaires (seulement les commentaires principaux, pas les réponses)
    comments = post.comments.filter(parent=None).select_related('user', 'user__profile').order_by('-created_at')
    
    # Construire la réponse JSON
    post_data = {
        'id': post.id,
        'user': {
            'id': post.user.id,
            'username': post.user.username,
            'full_name': f"{post.user.first_name} {post.user.last_name}".strip(),
            'avatar': post.user.profile.avatar.url if post.user.profile.avatar else None
        },
        'content': post.content,
        'image': post.image.url if post.image else None,
        'video': post.video.url if post.video else None,
        'voice_note': post.voice_note.url if post.voice_note else None,
        'location': post.location,
        'likes_count': post.likes_count,
        'comments_count': post.comments_count,
        'shares_count': post.shares_count,
        'created_at': post.created_at.strftime('%d/%m/%Y %H:%M'),
        'user_has_liked': post.reactions.filter(user=request.user).exists(),
        'comments': [
            {
                'id': comment.id,
                'user': comment.user.username,
                'user_avatar': comment.user.profile.avatar.url if comment.user.profile.avatar else None,
                'content': comment.content,
                'likes_count': comment.likes_count,
                'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M')
            }
            for comment in comments[:10]  # Limiter à 10 commentaires
        ]
    }
    
    return JsonResponse({
        'success': True,
        'post': post_data
    })


# ============================================
# VUE : MODIFIER UN COMMENTAIRE
# ============================================
@login_required(login_url='/login/')

@require_http_methods(["POST"])
def edit_comment(request, comment_id):
    """
    Vue pour modifier un commentaire existant.
    Seul le créateur du commentaire peut le modifier.
    """
    # Récupérer le commentaire
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Vérifier que l'utilisateur est bien le créateur du commentaire
    if comment.user != request.user:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'avez pas la permission de modifier ce commentaire.'
        }, status=403)
    
    # Récupérer le nouveau contenu
    new_content = request.POST.get('content', '').strip()
    
    # Validation
    if not new_content:
        return JsonResponse({
            'success': False,
            'error': 'Le commentaire ne peut pas être vide.'
        }, status=400)
    
    # Mettre à jour le commentaire
    comment.content = new_content
    comment.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Commentaire modifié avec succès !',
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'updated_at': comment.updated_at.strftime('%d/%m/%Y %H:%M')
        }
    })


# ============================================
# VUE : SUPPRIMER UN COMMENTAIRE
# ============================================
@login_required
@require_http_methods(["POST", "DELETE"])
def delete_comment(request, comment_id):
    """
    Vue pour supprimer un commentaire.
    Seul le créateur du commentaire peut le supprimer.
    """
    # Récupérer le commentaire
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Vérifier que l'utilisateur est bien le créateur
    if comment.user != request.user:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'avez pas la permission de supprimer ce commentaire.'
        }, status=403)
    
    # Récupérer le post pour mettre à jour le compteur
    post = comment.post
    
    # Supprimer le commentaire
    comment.delete()
    
    # Décrémenter le compteur
    post.comments_count = max(0, post.comments_count - 1)
    post.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Commentaire supprimé avec succès !',
        'comments_count': post.comments_count
    })
# ============================================
# ABONNEMENTS : VUES
# ============================================

@login_required(login_url='/login/')
def subscription_status(request):
    """Affiche le statut de l'abonnement de l'utilisateur"""
    try:
        subscription = request.user.subscription
        quota = request.user.quota
    except (Subscription.DoesNotExist, UsageQuota.DoesNotExist):
        return JsonResponse({
            'success': False,
            'error': 'Profil incomplet'
        }, status=500)
    
    return JsonResponse({
        'success': True,
        'subscription': {
            'plan': subscription.plan,
            'plan_display': subscription.get_plan_display(),
            'is_active': subscription.is_active,
            'is_premium': subscription.is_premium,
            'is_business': subscription.is_business,
            'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
            'auto_renew': subscription.auto_renew,
        },
        'quota': {
            'posts_this_month': quota.posts_this_month,
            'messages_this_month': quota.messages_this_month,
            'trips_created': quota.trips_created,
            'groups_joined': quota.groups_joined,
            'events_created_this_month': quota.events_created_this_month,
        },
        'limits': settings.SUBSCRIPTION_LIMITS[subscription.plan]
    })


@login_required(login_url='/login/')
def manage_subscription(request):
    """Page de gestion de l'abonnement"""
    try:
        subscription = request.user.subscription
        payments = PaymentHistory.objects.filter(user=request.user).order_by('-created_at')[:10]
    except Subscription.DoesNotExist:
        return redirect('upgrade')
    
    context = {
        'subscription': subscription,
        'payments': payments,
    }
    return render(request, 'subscription/manage.html', context)


@login_required(login_url='/login/')
@require_http_methods(["POST"])
def cancel_subscription(request):
    """Annuler le renouvellement automatique"""
    try:
        subscription = request.user.subscription
        subscription.cancel()
        
        messages.success(request, '✅ Le renouvellement automatique a été annulé. Votre abonnement restera actif jusqu\'à la date d\'expiration.')
        return redirect('manage_subscription')
    except Subscription.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Aucun abonnement trouvé'
        }, status=404)
# ============================================
# PAIEMENTS : STRIPE UNIQUEMENT
# ============================================

# Initialiser Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required(login_url='/login/')
def checkout(request, plan, duration='monthly'):
    """
    Page de checkout pour le paiement Stripe uniquement
    """
    # Calculer le prix
    if plan.lower() == 'premium':
        price_eur = 9.99 if duration == 'monthly' else 99
        duration_months = 1 if duration == 'monthly' else 12
    elif plan.lower() == 'business':
        price_eur = 29.99 if duration == 'monthly' else 299
        duration_months = 1 if duration == 'monthly' else 12
    else:
        messages.error(request, '❌ Plan invalide')
        return redirect('upgrade')
    
    # IMPORTANT: Vérifier que la clé publique Stripe existe
    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    if not stripe_public_key:
        messages.error(request, '❌ Configuration Stripe manquante. Contactez le support.')
        return redirect('upgrade')
    
    # Debug log
    print(f"[CHECKOUT] Rendering checkout for {plan} - {duration}")
    print(f"[CHECKOUT] Stripe public key: {stripe_public_key[:20]}...")
    
    context = {
        'plan': plan.upper(),
        'plan_display': 'Premium' if plan.lower() == 'premium' else 'Business',
        'duration': duration,
        'duration_display': 'Mensuel' if duration == 'monthly' else 'Annuel',
        'duration_months': duration_months,
        'price_eur': price_eur,
        'stripe_public_key': stripe_public_key,
    }
    return render(request, 'subscription/checkout.html', context)


@login_required(login_url='/login/')
@require_http_methods(["POST"])
def process_stripe_payment(request):
    """
    Traiter le paiement Stripe avec gestion d'erreurs détaillée
    """
    try:
        # Vérifier la configuration Stripe
        if not settings.STRIPE_SECRET_KEY:
            return JsonResponse({
                'success': False, 
                'error': 'Configuration Stripe manquante'
            }, status=500)
        
        # Récupérer les données
        plan = request.POST.get('plan', '').upper()
        duration = request.POST.get('duration', 'monthly')
        
        print(f"[STRIPE] Processing payment for {request.user.username}: {plan} - {duration}")
        
        # Validation du plan
        if plan not in ['PREMIUM', 'BUSINESS']:
            return JsonResponse({
                'success': False, 
                'error': 'Plan invalide'
            }, status=400)
        
        # Calculer le prix et la durée
        if plan == 'PREMIUM':
            amount = 999 if duration == 'monthly' else 9900  # en centimes
            duration_months = 1 if duration == 'monthly' else 12
        elif plan == 'BUSINESS':
            amount = 2999 if duration == 'monthly' else 29900
            duration_months = 1 if duration == 'monthly' else 12
        
        # Créer ou récupérer le client Stripe
        subscription = request.user.subscription
        
        if not subscription.stripe_customer_id:
            print(f"[STRIPE] Creating new customer for {request.user.email}")
            try:
                customer = stripe.Customer.create(
                    email=request.user.email,
                    name=f"{request.user.first_name} {request.user.last_name}",
                    metadata={'user_id': request.user.id}
                )
                subscription.stripe_customer_id = customer.id
                subscription.save()
                print(f"[STRIPE] Customer created: {customer.id}")
            except stripe.error.StripeError as e:
                print(f"[STRIPE ERROR] Customer creation failed: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'error': f'Erreur Stripe: {str(e)}'
                }, status=500)
        
        # Créer le PaymentIntent
        print(f"[STRIPE] Creating PaymentIntent: {amount} cents")
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency='eur',
                customer=subscription.stripe_customer_id,
                metadata={
                    'user_id': request.user.id,
                    'plan': plan,
                    'duration_months': duration_months
                },
                automatic_payment_methods={'enabled': True},
            )
            print(f"[STRIPE] PaymentIntent created: {intent.id}")
        except stripe.error.StripeError as e:
            print(f"[STRIPE ERROR] PaymentIntent failed: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Erreur création paiement: {str(e)}'
            }, status=500)
        
        # Créer l'historique de paiement
        payment = PaymentHistory.objects.create(
            user=request.user,
            subscription=subscription,
            amount=Decimal(amount) / 100,
            currency='EUR',
            status='PENDING',
            stripe_payment_intent_id=intent.id,
            plan_purchased=plan,
            duration_months=duration_months,
            payment_method='STRIPE'
        )
        print(f"[STRIPE] Payment history created: {payment.id}")
        
        return JsonResponse({
            'success': True,
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id
        })
        
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }, status=500)


@login_required(login_url='/login/')
def payment_success(request):
    """Page de succès après paiement"""
    messages.success(request, '✅ Paiement réussi ! Votre abonnement a été activé.')
    return redirect('manage_subscription')


@login_required(login_url='/login/')
def payment_failure(request):
    """Page d'échec après paiement"""
    messages.error(request, '❌ Le paiement a échoué. Veuillez réessayer.')
    return redirect('upgrade')


# ============================================
# WEBHOOKS - STRIPE UNIQUEMENT
# ============================================

@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Webhook Stripe pour gérer les événements de paiement
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        print("[WEBHOOK ERROR] Invalid payload")
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        print("[WEBHOOK ERROR] Invalid signature")
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    print(f"[WEBHOOK] Received event: {event['type']}")
    
    # Gérer les différents types d'événements
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        
        # Récupérer les métadonnées
        user_id = int(payment_intent['metadata']['user_id'])
        plan = payment_intent['metadata']['plan']
        duration_months = int(payment_intent['metadata']['duration_months'])
        
        print(f"[WEBHOOK] Payment succeeded for user {user_id}: {plan} - {duration_months} months")
        
        try:
            user = User.objects.get(id=user_id)
            subscription = user.subscription
            
            # Mettre à jour l'abonnement
            if plan == 'PREMIUM':
                subscription.upgrade_to_premium(duration_months=duration_months, payment_method='STRIPE')
            elif plan == 'BUSINESS':
                subscription.upgrade_to_business(duration_months=duration_months, payment_method='STRIPE')
            
            subscription.stripe_subscription_id = payment_intent.get('subscription')
            subscription.save()
            
            print(f"[WEBHOOK] Subscription updated for user {user_id}")
            
            # Mettre à jour l'historique de paiement
            payment = PaymentHistory.objects.filter(
                stripe_payment_intent_id=payment_intent['id']
            ).first()
            if payment:
                payment.status = 'COMPLETED'
                payment.save()
                print(f"[WEBHOOK] Payment history updated: {payment.id}")
                
        except User.DoesNotExist:
            print(f"[WEBHOOK ERROR] User {user_id} not found")
    
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        
        print(f"[WEBHOOK] Payment failed: {payment_intent['id']}")
        
        # Marquer le paiement comme échoué
        payment = PaymentHistory.objects.filter(
            stripe_payment_intent_id=payment_intent['id']
        ).first()
        if payment:
            payment.status = 'FAILED'
            payment.save()
            print(f"[WEBHOOK] Payment marked as failed: {payment.id}")
    
    return JsonResponse({'status': 'success'})


# ============================================
# TEST ENDPOINT (Development only)
# ============================================

@login_required
def test_stripe(request):
    """Test endpoint to verify Stripe configuration"""
    try:
        # Test API key
        customers = stripe.Customer.list(limit=1)
        return JsonResponse({
            'success': True,
            'message': 'Stripe API working correctly',
            'api_key_prefix': settings.STRIPE_SECRET_KEY[:7] + '...',
            'public_key_prefix': settings.STRIPE_PUBLIC_KEY[:7] + '...'
        })
    except stripe.error.AuthenticationError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid API key'
        }, status=401)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    
    # ============================================
# VUES PREMIUM/BUSINESS : WALLET
# ============================================

from core.decorators import premium_required, business_required
from .forms import (WalletForm, WalletTransactionForm, AddFundsForm, 
                    BucketListForm, TripForm, TripExpenseForm)
from .models import Wallet, WalletTransaction, BucketList, Trip
from .ai_services_gemini import (generate_destination_recommendations, 
                                  generate_bucket_list_description,
                                  generate_trip_itinerary,
                                  generate_travel_tips,
                                  analyze_spending_pattern)

@login_required(login_url='/login/')
@premium_required
def wallet_dashboard(request):
    """
    Tableau de bord du portefeuille (PREMIUM/BUSINESS uniquement)
    """
    # Récupérer ou créer le wallet
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Récupérer les transactions
    transactions = wallet.transactions.all()[:20]
    
    # Statistiques
    total_transactions = wallet.transactions.count()
    total_deposits = wallet.transactions.filter(transaction_type='DEPOSIT').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    total_expenses = wallet.transactions.filter(transaction_type='EXPENSE').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    # Analyse IA des dépenses
    ai_analysis = None
    if total_transactions > 5:
        ai_analysis = analyze_spending_pattern(wallet.transactions.all()[:20])
    
    context = {
        'wallet': wallet,
        'transactions': transactions,
        'total_transactions': total_transactions,
        'total_deposits': total_deposits,
        'total_expenses': total_expenses,
        'ai_analysis': ai_analysis,
    }
    return render(request, 'premium/wallet_dashboard.html', context)


@login_required(login_url='/login/')
@premium_required
@require_http_methods(["POST"])
def wallet_add_funds(request):
    """
    Ajouter des fonds au portefeuille
    """
    form = AddFundsForm(request.POST)
    
    if form.is_valid():
        amount = form.cleaned_data['amount']
        wallet = request.user.wallet
        
        # Ajouter les fonds
        wallet.add_funds(amount)
        
        # Créer une transaction
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='DEPOSIT',
            amount=amount,
            description=f'Dépôt de fonds'
        )
        
        messages.success(request, f'✅ {amount} {wallet.currency} ajoutés à votre portefeuille !')
        return redirect('wallet_dashboard')
    
    messages.error(request, '❌ Montant invalide')
    return redirect('wallet_dashboard')


@login_required(login_url='/login/')
@premium_required
def wallet_transactions(request):
    """
    Liste complète des transactions
    """
    wallet = request.user.wallet
    transactions = wallet.transactions.all()
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'wallet': wallet,
        'page_obj': page_obj,
    }
    return render(request, 'premium/wallet_transactions.html', context)


# ============================================
# VUES PREMIUM/BUSINESS : BUCKET LIST
# ============================================

@login_required(login_url='/login/')
@premium_required
def bucket_list(request):
    """
    Liste des destinations de rêve (PREMIUM/BUSINESS uniquement)
    """
    items = BucketList.objects.filter(user=request.user)
    
    # Filtres
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        items = items.filter(status=status_filter)
    
    # Statistiques
    total_destinations = items.count()
    completed = items.filter(status='COMPLETED').count()
    planned = items.filter(status='PLANNED').count()
    
    context = {
        'bucket_items': items,
        'status_filter': status_filter,
        'total_destinations': total_destinations,
        'completed': completed,
        'planned': planned,
    }
    return render(request, 'premium/bucket_list.html', context)


@login_required(login_url='/login/')
@premium_required
def bucket_list_create(request):
    """
    Créer un nouvel élément de bucket list
    """
    if request.method == 'POST':
        form = BucketListForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            
            # Générer une description IA si vide
            if not item.description:
                item.description = generate_bucket_list_description(
                    item.destination, 
                    item.country
                )
            
            item.save()
            messages.success(request, f'✅ {item.destination} ajouté à votre bucket list !')
            return redirect('bucket_list')
    else:
        form = BucketListForm()
    
    context = {'form': form}
    return render(request, 'premium/bucket_list_form.html', context)


@login_required(login_url='/login/')
@premium_required
def bucket_list_edit(request, item_id):
    """
    Modifier un élément de bucket list
    """
    item = get_object_or_404(BucketList, id=item_id, user=request.user)
    
    if request.method == 'POST':
        form = BucketListForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Destination mise à jour !')
            return redirect('bucket_list')
    else:
        form = BucketListForm(instance=item)
    
    context = {'form': form, 'item': item}
    return render(request, 'premium/bucket_list_form.html', context)


@login_required(login_url='/login/')
@premium_required
@require_http_methods(["POST"])
def bucket_list_delete(request, item_id):
    """
    Supprimer un élément de bucket list
    """
    item = get_object_or_404(BucketList, id=item_id, user=request.user)
    destination_name = item.destination
    item.delete()
    
    messages.success(request, f'✅ {destination_name} supprimé de votre bucket list')
    return redirect('bucket_list')


@login_required(login_url='/login/')
@premium_required
@require_http_methods(["POST"])
def bucket_list_mark_visited(request, item_id):
    """
    Marquer une destination comme visitée
    """
    item = get_object_or_404(BucketList, id=item_id, user=request.user)
    item.mark_as_visited()
    
    messages.success(request, f'🎉 Félicitations ! Vous avez visité {item.destination} !')
    return redirect('bucket_list')


# ============================================
# VUES PREMIUM/BUSINESS : TRIPS
# ============================================

@login_required(login_url='/login/')
@premium_required
def trips_list(request):
    """
    Liste des voyages (PREMIUM/BUSINESS uniquement)
    """
    trips = Trip.objects.filter(user=request.user)
    
    # Statistiques
    total_trips = trips.count()
    ongoing = trips.filter(status='ONGOING').count()
    completed = trips.filter(status='COMPLETED').count()
    
    context = {
        'trips': trips,
        'total_trips': total_trips,
        'ongoing': ongoing,
        'completed': completed,
    }
    return render(request, 'premium/trips_list.html', context)


@login_required(login_url='/login/')
@premium_required
def trip_create(request):
    """
    Créer un nouveau voyage
    """
    if request.method == 'POST':
        form = TripForm(request.POST, user=request.user)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.user = request.user
            trip.save()
            
            messages.success(request, f'✅ Voyage "{trip.title}" créé avec succès !')
            return redirect('trips_list')
    else:
        form = TripForm(user=request.user)
    
    context = {'form': form}
    return render(request, 'premium/trip_form.html', context)


@login_required(login_url='/login/')
@premium_required
def trip_detail(request, trip_id):
    """
    Détails d'un voyage avec itinéraire IA
    """
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    
    # Générer un itinéraire IA
    from .mongo import get_db
    db = get_db()
    user_profile = db.profiles.find_one({'user_id': request.user.id})
    interests = user_profile.get('interests', []) if user_profile else []
    
    itinerary = generate_trip_itinerary(
        trip.destination, 
        trip.duration_days, 
        interests
    )
    
    # Conseils de voyage
    nationality = user_profile.get('nationality', '') if user_profile else ''
    travel_tips = generate_travel_tips(trip.destination, nationality)
    
    context = {
        'trip': trip,
        'itinerary': itinerary,
        'travel_tips': travel_tips,
    }
    return render(request, 'premium/trip_detail.html', context)


@login_required(login_url='/login/')
@premium_required
@require_http_methods(["POST"])
def trip_add_expense(request, trip_id):
    """
    Ajouter une dépense à un voyage
    """
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    form = TripExpenseForm(request.POST)
    
    if form.is_valid():
        amount = form.cleaned_data['amount']
        description = form.cleaned_data['description']
        deduct_from_wallet = form.cleaned_data['deduct_from_wallet']
        
        # Ajouter la dépense au voyage
        trip.actual_spent += amount
        trip.save()
        
        # Déduire du wallet si demandé
        if deduct_from_wallet and hasattr(request.user, 'wallet'):
            wallet = request.user.wallet
            if wallet.withdraw_funds(amount):
                # Créer une transaction
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='EXPENSE',
                    amount=amount,
                    description=description,
                    related_trip=trip
                )
                messages.success(request, f'✅ Dépense ajoutée et déduite du portefeuille')
            else:
                messages.warning(request, '⚠️ Dépense ajoutée mais solde insuffisant dans le portefeuille')
        else:
            messages.success(request, f'✅ Dépense ajoutée au voyage')
        
        return redirect('trip_detail', trip_id=trip.id)
    
    messages.error(request, '❌ Formulaire invalide')
    return redirect('trip_detail', trip_id=trip.id)


# ============================================
# VUE IA : RECOMMANDATIONS DE DESTINATIONS
# ============================================

@login_required(login_url='/login/')
@premium_required
def ai_recommendations(request):
    """
    Recommandations IA de destinations (PREMIUM/BUSINESS uniquement)
    """
    from .mongo import get_db
    db = get_db()
    user_profile = db.profiles.find_one({'user_id': request.user.id})
    
    # Récupérer le solde du wallet
    wallet_balance = None
    if hasattr(request.user, 'wallet'):
        wallet_balance = float(request.user.wallet.balance)
    
    # Générer les recommandations
    recommendations_result = generate_destination_recommendations(
        user_profile or {},
        wallet_balance=wallet_balance,
        max_recommendations=6
    )
    
    context = {
        'recommendations': recommendations_result.get('recommendations', []),
        'success': recommendations_result.get('success', False),
        'error': recommendations_result.get('error'),
        'wallet_balance': wallet_balance,
    }
    return render(request, 'premium/ai_recommendations.html', context)


@login_required(login_url='/login/')
@premium_required
@require_http_methods(["POST"])
def ai_add_to_bucket_list(request):
    """
    Ajouter une recommandation IA directement à la bucket list
    """
    try:
        data = json.loads(request.body)
        
        # Créer l'élément de bucket list depuis la recommandation
        item = BucketList.objects.create(
            user=request.user,
            destination=data.get('destination'),
            country=data.get('country'),
            description=data.get('description'),
            estimated_budget=data.get('estimated_budget'),
            currency=data.get('currency', 'EUR'),
            priority=data.get('priority', 3),
            ai_tags=data.get('tags', []),
            ai_recommendations=data.get('why_recommended', ''),
            status='PLANNED'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'{item.destination} ajouté à votre bucket list !',
            'item_id': item.id
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ============================================
# CHAT API ENDPOINTS
# ============================================

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_chats(request):
    """Récupère la liste des chats de l'utilisateur"""
    try:
        from .models import ChatRoom
        
        # Récupérer tous les chats de l'utilisateur
        user_chats = ChatRoom.objects.filter(
            participants=request.user
        ).prefetch_related('participants', 'last_message_by').order_by('-last_message_at', '-updated_at')
        
        chats_data = []
        for chat in user_chats:
            # Pour les chats privés, récupérer l'autre participant
            if chat.room_type == 'private':
                other_participant = chat.get_other_participant(request.user)
                if other_participant:
                    chat_name = f"{other_participant.first_name} {other_participant.last_name}".strip() or other_participant.username
                    avatar_url = None
                    if hasattr(other_participant, 'profile') and other_participant.profile.avatar:
                        avatar_url = other_participant.profile.avatar.url
                else:
                    chat_name = "Chat supprimé"
                    avatar_url = None
            else:
                chat_name = chat.name or f"Groupe #{chat.id}"
                avatar_url = None  # TODO: Ajouter avatar de groupe
            
            # Compter les messages non lus
            unread_count = chat.get_unread_count(request.user)
            
            chat_data = {
                'id': chat.id,
                'name': chat_name,
                'room_type': chat.room_type,
                'last_message': chat.last_message,
                'last_message_at': chat.last_message_at.isoformat() if chat.last_message_at else None,
                'last_message_by': chat.last_message_by.username if chat.last_message_by else None,
                'unread_count': unread_count,
                'avatar_url': avatar_url,
                'participants_count': chat.participants.count()
            }
            
            # Add other participant data for private chats
            if chat.room_type == 'private' and other_participant:
                chat_data['other_participant'] = {
                    'id': other_participant.id,
                    'username': other_participant.username,
                    'first_name': other_participant.first_name,
                    'last_name': other_participant.last_name,
                    'avatar': avatar_url
                }
            
            chats_data.append(chat_data)
        
        return JsonResponse(chats_data, safe=False)
        
    except Exception as e:
        return JsonResponse([], safe=False)


@login_required(login_url='/login/')
def get_user_chats_session(request):
    """Récupère la liste des chats de l'utilisateur avec authentification par session"""
    try:
        from .models import ChatRoom
        
        # Récupérer tous les chats de l'utilisateur
        user_chats = ChatRoom.objects.filter(
            participants=request.user
        ).prefetch_related('participants', 'last_message_by').order_by('-last_message_at', '-updated_at')
        
        chats_data = []
        for chat in user_chats:
            # Pour les chats privés, récupérer l'autre participant
            if chat.room_type == 'private':
                other_participant = chat.get_other_participant(request.user)
                if other_participant:
                    chat_name = f"{other_participant.first_name} {other_participant.last_name}".strip() or other_participant.username
                    avatar_url = None
                    if hasattr(other_participant, 'profile') and other_participant.profile.avatar:
                        avatar_url = other_participant.profile.avatar.url
                else:
                    chat_name = "Chat supprimé"
                    avatar_url = None
            else:
                chat_name = chat.name or f"Groupe #{chat.id}"
                avatar_url = None  # TODO: Ajouter avatar de groupe
            
            # Compter les messages non lus
            unread_count = chat.get_unread_count(request.user)
            
            chat_data = {
                'id': chat.id,
                'name': chat_name,
                'room_type': chat.room_type,
                'last_message': chat.last_message,
                'last_message_at': chat.last_message_at.isoformat() if chat.last_message_at else None,
                'last_message_by': chat.last_message_by.username if chat.last_message_by else None,
                'unread_count': unread_count,
                'avatar_url': avatar_url,
                'participants_count': chat.participants.count()
            }
            
            # Add other participant data for private chats
            if chat.room_type == 'private' and other_participant:
                chat_data['other_participant'] = {
                    'id': other_participant.id,
                    'username': other_participant.username,
                    'first_name': other_participant.first_name,
                    'last_name': other_participant.last_name,
                    'avatar': avatar_url
                }
            
            chats_data.append(chat_data)
        
        return JsonResponse(chats_data, safe=False)
        
    except Exception as e:
        return JsonResponse([], safe=False)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_private_chat(request):
    """Crée un chat privé avec un autre utilisateur"""
    try:
        from .models import ChatRoom
        
        other_user_id = request.data.get('user_id')
        if not other_user_id:
            return JsonResponse({
                'success': False,
                'error': 'ID utilisateur requis'
            }, status=400)
        
        try:
            other_user = User.objects.get(id=other_user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Utilisateur introuvable'
            }, status=404)
        
        # Vérifier si un chat privé existe déjà entre ces deux utilisateurs
        existing_chat = ChatRoom.objects.filter(
            room_type='private',
            participants=request.user
        ).filter(
            participants=other_user
        ).first()
        
        if existing_chat:
            return JsonResponse({
                'success': True,
                'chat_id': existing_chat.id,
                'message': 'Chat existant trouvé'
            })
        
        # Créer un nouveau chat privé
        chat_room = ChatRoom.objects.create(
            room_type='private',
            created_by=request.user
        )
        chat_room.participants.add(request.user, other_user)
        
        return JsonResponse({
            'success': True,
            'chat_id': chat_room.id,
            'message': 'Chat privé créé'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_messages(request, chat_id):
    """Récupère les messages d'un chat avec sentiment"""
    try:
        from .models import ChatRoom, Message
        
        # Vérifier l'accès au chat
        try:
            chat_room = ChatRoom.objects.get(id=chat_id, participants=request.user)
        except ChatRoom.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Chat introuvable ou accès refusé'
            }, status=404)
        
        # Récupérer les messages avec pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        
        messages = Message.objects.filter(
            chat_room=chat_room
        ).select_related('sender', 'sender__profile').prefetch_related('files').order_by('-created_at')
        
        paginator = Paginator(messages, page_size)
        page_obj = paginator.get_page(page)
        
        messages_data = []
        for message in page_obj:
            avatar_url = None
            if hasattr(message.sender, 'profile') and message.sender.profile.avatar:
                avatar_url = message.sender.profile.avatar.url
            
            # Prepare files data
            files_data = []
            for message_file in message.files.all():
                files_data.append({
                    'id': message_file.id,
                    'url': message_file.file_url,
                    'original_name': message_file.original_name,
                    'file_type': message_file.file_type,
                    'file_size': message_file.file_size,
                    'is_image': message_file.is_image,
                    'is_video': message_file.is_video,
                    'is_audio': message_file.is_audio
                })
            
            messages_data.append({
                'id': message.id,
                'content': message.content,
                'message_type': message.message_type,
                'sender': {
                    'id': message.sender.id,
                    'username': message.sender.username,
                    'full_name': f"{message.sender.first_name} {message.sender.last_name}".strip() or message.sender.username,
                    'avatar_url': avatar_url
                },
                'created_at': message.created_at.isoformat(),
                'is_read': message.is_read_by(request.user),
                'files': files_data,
                'image_url': message.image.url if message.image else None,
                'file_url': message.file.url if message.file else None,
                'voice_url': message.voice_note.url if message.voice_note else None,
                # ✨ Include sentiment in response
                'sentiment': {
                    'label': message.sentiment_label,
                    'score': message.sentiment_score,
                    'emoji': message.sentiment_emoji
                }
            })
        
        # Marquer les messages comme lus
        unread_messages = messages.filter(chat_room=chat_room).exclude(sender=request.user)
        for message in unread_messages:
            message.mark_as_read(request.user)
        
        return JsonResponse({
            'success': True,
            'messages': list(reversed(messages_data)),  # Inverser pour avoir les plus anciens en premier
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'total_pages': paginator.num_pages,
            'current_page': page
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request, chat_id):
    """Envoie un message dans un chat avec analyse de sentiment"""
    try:
        from .models import ChatRoom, Message, MessageFile
        import mimetypes
        
        # Vérifier l'accès au chat
        try:
            chat_room = ChatRoom.objects.get(id=chat_id, participants=request.user)
        except ChatRoom.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Chat introuvable ou accès refusé'
            }, status=404)
        
        content = request.data.get('content', '').strip() if hasattr(request, 'data') else request.POST.get('content', '').strip()
        message_type = request.data.get('message_type', 'text') if hasattr(request, 'data') else request.POST.get('message_type', 'text')
        
        # Get uploaded files
        uploaded_files = request.FILES.getlist('files') if 'files' in request.FILES else []
        
        # Check if we have content or files
        if not content and not uploaded_files and message_type == 'text':
            return JsonResponse({
                'success': False,
                'error': 'Le contenu du message ou des fichiers sont requis'
            }, status=400)
        
        # Determine message type based on files
        if uploaded_files:
            # Check if all files are images
            all_images = all(file.content_type.startswith('image/') for file in uploaded_files)
            message_type = 'image' if all_images else 'file'
        
        # ✨ Analyze sentiment for text messages
        sentiment = {'label': 'NEUTRAL', 'score': 0.0, 'emoji': '😐'}
        if content.strip():  # Only analyze if there's text content
            try:
                sentiment = sentiment_analyzer.analyze(content)
                logger.info(f"💬 Sentiment analyzed for message: {sentiment['label']} ({sentiment['score']}) {sentiment['emoji']}")
            except Exception as e:
                logger.error(f"Sentiment analysis failed: {e}")
                # Continue without sentiment if analysis fails
        
        # Créer le message avec sentiment
        message = Message.objects.create(
            chat_room=chat_room,
            sender=request.user,
            content=content,
            message_type=message_type,
            sentiment_label=sentiment['label'],
            sentiment_score=sentiment['score'],
            sentiment_emoji=sentiment['emoji']
        )
        
        # Handle multiple file uploads
        message_files = []
        for uploaded_file in uploaded_files:
            # Get file type
            file_type = uploaded_file.content_type or mimetypes.guess_type(uploaded_file.name)[0] or 'application/octet-stream'
            
            # Create MessageFile instance
            message_file = MessageFile.objects.create(
                message=message,
                file=uploaded_file,
                original_name=uploaded_file.name,
                file_type=file_type,
                file_size=uploaded_file.size
            )
            message_files.append(message_file)
        
        # Gérer les fichiers uploadés (legacy support)
        if 'image' in request.FILES:
            message.image = request.FILES['image']
            message.message_type = 'image'
        elif 'file' in request.FILES:
            message.file = request.FILES['file']
            message.message_type = 'file'
        elif 'voice_note' in request.FILES:
            message.voice_note = request.FILES['voice_note']
            message.message_type = 'voice'
        
        message.save()
        
        # Mettre à jour le dernier message du chat
        chat_room.last_message = content or f"[{message.get_message_type_display()}]"
        chat_room.last_message_at = message.created_at
        chat_room.last_message_by = request.user
        chat_room.save()
        
        # Préparer la réponse
        avatar_url = None
        if hasattr(request.user, 'profile') and request.user.profile.avatar:
            avatar_url = request.user.profile.avatar.url
        
        # Prepare files data for response
        files_data = []
        for message_file in message_files:
            files_data.append({
                'id': message_file.id,
                'url': message_file.file_url,
                'original_name': message_file.original_name,
                'file_type': message_file.file_type,
                'file_size': message_file.file_size,
                'is_image': message_file.is_image,
                'is_video': message_file.is_video,
                'is_audio': message_file.is_audio
            })
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'message_type': message.message_type,
                'sender': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                    'avatar_url': avatar_url
                },
                'created_at': message.created_at.isoformat(),
                'files': files_data,
                'image_url': message.image.url if message.image else None,
                'file_url': message.file.url if message.file else None,
                'voice_url': message.voice_note.url if message.voice_note else None,
                # ✨ Include sentiment in response
                'sentiment': {
                    'label': message.sentiment_label,
                    'score': message.sentiment_score,
                    'emoji': message.sentiment_emoji
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_message(request, chat_id, message_id):
    """Supprime un message dans un chat"""
    try:
        from .models import ChatRoom, Message
        
        # Vérifier l'accès au chat
        try:
            chat_room = ChatRoom.objects.get(id=chat_id, participants=request.user)
        except ChatRoom.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Chat introuvable ou accès refusé'
            }, status=404)
        
        # Vérifier que le message existe et appartient à l'utilisateur
        try:
            message = Message.objects.get(
                id=message_id,
                chat_room=chat_room,
                sender=request.user
            )
        except Message.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Message introuvable ou vous n\'êtes pas autorisé à le supprimer'
            }, status=404)
        
        # Supprimer le message
        message.delete()
        
        # Mettre à jour le dernier message du chat si nécessaire
        last_message = Message.objects.filter(chat_room=chat_room).order_by('-created_at').first()
        if last_message:
            chat_room.last_message = last_message.content or f"[{last_message.get_message_type_display()}]"
            chat_room.last_message_at = last_message.created_at
            chat_room.last_message_by = last_message.sender
        else:
            chat_room.last_message = ""
            chat_room.last_message_at = None
            chat_room.last_message_by = None
        chat_room.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Message supprimé avec succès'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users_for_chat(request):
    """Recherche d'utilisateurs pour créer un chat"""
    try:
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return JsonResponse([], safe=False)
        
        # Rechercher les utilisateurs
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:20]  # Limiter à 20 résultats
        
        users_data = []
        for user in users:
            avatar_url = None
            if hasattr(user, 'profile') and user.profile.avatar:
                avatar_url = user.profile.avatar.url
            
            users_data.append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'avatar': avatar_url
            })
        
        return JsonResponse(users_data, safe=False)
        
    except Exception as e:
        return JsonResponse([], safe=False)
