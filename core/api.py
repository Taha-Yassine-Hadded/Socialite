from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Post
from django.contrib.auth.models import User

@login_required
def posts_with_location(request):
    """
    API pour récupérer les posts avec des informations de localisation
    Supporte les filtres par pays et par utilisateur
    """
    # Récupérer les filtres
    country_filter = request.GET.get('country', '')
    user_filter = request.GET.get('user_id', '')
    
    # Construire la requête de base
    query = Post.objects.filter(
        # Au moins une information de localisation doit être présente
        (models.Q(location__isnull=False) & ~models.Q(location='')) | 
        (models.Q(detected_country__isnull=False) & ~models.Q(detected_country='')) |
        (models.Q(latitude__isnull=False) & models.Q(longitude__isnull=False))
    )
    
    # Appliquer les filtres
    if country_filter:
        query = query.filter(detected_country=country_filter)
    
    if user_filter:
        try:
            user_id = int(user_filter)
            query = query.filter(user_id=user_id)
        except (ValueError, TypeError):
            pass
    
    # Récupérer les posts avec leurs utilisateurs
    posts = query.select_related('user').order_by('-created_at')[:50]  # Limiter à 50 posts
    
    # Formater les données
    posts_data = []
    for post in posts:
        post_data = {
            'id': post.id,
            'content': post.content,
            'location': post.location,
            'detected_country': post.detected_country,
            'detected_landmark': post.detected_landmark,
            'latitude': post.latitude,
            'longitude': post.longitude,
            'created_at': post.created_at.isoformat(),
            'user_id': post.user.id,
            'user_name': f"{post.user.first_name} {post.user.last_name}",
            'user_username': post.user.username,
        }
        
        # Ajouter l'URL de l'image si elle existe
        if post.image:
            post_data['image'] = post.image.url
        
        # Ajouter l'avatar de l'utilisateur s'il existe
        try:
            from django.db import connections
            with connections['default'].cursor() as cursor:
                cursor.execute(
                    "SELECT profile_image FROM profiles WHERE user_id = %s",
                    [post.user.id]
                )
                result = cursor.fetchone()
                if result and result[0]:
                    post_data['user_avatar'] = result[0]
        except Exception:
            pass
        
        posts_data.append(post_data)
    
    return JsonResponse({
        'success': True,
        'posts': posts_data
    })