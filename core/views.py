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
from django.db.models import Q
from .models import Post, Comment, Reaction, Share, UserProfile
import json

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
    """
    # Récupérer tous les posts publics + posts de l'utilisateur
    posts = Post.objects.filter(
        Q(visibility='public') | Q(user=request.user)
    ).select_related('user', 'user__profile').prefetch_related(
        'comments', 'comments__user', 'comments__user__profile', 
        'comments__reactions', 'reactions', 'post_shares'
    ).order_by('-created_at')
    
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
    
    context = {
        'posts': posts,
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
@login_required
def profile_view(request, slug=None):
    """Affiche le profil d'un utilisateur avec ses posts (via son slug unique)"""
    if slug:
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
    
    context = {
        'user': user,
        'profile': user.profile,
        'user_posts': user_posts,
        'posts_count': user_posts.count(),
    }
    return render(request, 'profile.html', context)
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
                
                # Mettre à jour les données MongoDB
                mongo_updates = {
                    'travel_type': request.POST.getlist('travel_type'),
                    'travel_budget': request.POST.get('travel_budget', ''),
                    'gender': request.POST.get('gender', ''),
                    'languages': request.POST.getlist('languages'),
                    'nationality': request.POST.get('nationality', ''),
                    'interests': request.POST.getlist('interests'),
                    'visited_countries': request.POST.getlist('visited_countries'),
                }
                
                db.profiles.update_one(
                    {'user_id': request.user.id},
                    {'$set': mongo_updates}
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
# VUE : CRÉER UN POST
# ============================================
@login_required
def create_post(request):
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
        
        # Retourner une réponse JSON (succès)
        return JsonResponse({
            'success': True,
            'message': 'Post créé avec succès !',
            'post_id': post.id
        })
    
    # Si GET : afficher le formulaire de création
    return render(request, 'create_post.html')
    # ============================================
# VUE : AFFICHER LE FIL D'ACTUALITÉ
# ============================================
@login_required
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
# VUE : SUPPRIMER UN POST
# ============================================
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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