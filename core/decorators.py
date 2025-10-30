from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse

def premium_required(view_func):
    """
    Décorateur pour vérifier que l'utilisateur a un abonnement Premium ou Business
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '🔒 Vous devez être connecté pour accéder à cette fonctionnalité.')
            return redirect('login_page')
        
        if not hasattr(request.user, 'subscription'):
            messages.error(request, '⚠️ Une erreur est survenue. Veuillez contacter le support.')
            return redirect('feed')
        
        if not request.user.subscription.is_premium:
            messages.warning(request, '⭐ Cette fonctionnalité est réservée aux abonnés Premium et Business.')
            return redirect('upgrade')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def business_required(view_func):
    """
    Décorateur pour vérifier que l'utilisateur a un abonnement Business
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '🔒 Vous devez être connecté pour accéder à cette fonctionnalité.')
            return redirect('login_page')
        
        if not hasattr(request.user, 'subscription'):
            messages.error(request, '⚠️ Une erreur est survenue. Veuillez contacter le support.')
            return redirect('feed')
        
        if not request.user.subscription.is_business:
            messages.warning(request, '🏢 Cette fonctionnalité est réservée aux abonnés Business.')
            return redirect('upgrade')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def check_quota(quota_type):
    """
    Décorateur pour vérifier les quotas avant une action
    quota_type: 'post', 'message', 'trip', 'group', 'event'
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'error': 'Vous devez être connecté.'
                }, status=401)
            
            # Les utilisateurs Premium n'ont pas de limites
            if request.user.subscription.is_premium:
                return view_func(request, *args, **kwargs)
            
            # Vérifier le quota
            quota = request.user.quota
            
            can_proceed = False
            error_message = ''
            
            if quota_type == 'post':
                can_proceed = quota.can_create_post()
                error_message = f'🚫 Limite atteinte : {quota.posts_this_month}/10 posts ce mois. Passez à Premium pour des posts illimités !'
            
            elif quota_type == 'message':
                can_proceed = quota.can_send_message()
                error_message = f'🚫 Limite atteinte : {quota.messages_this_month}/50 messages ce mois. Passez à Premium pour des messages illimités !'
            
            elif quota_type == 'trip':
                can_proceed = quota.can_create_trip()
                error_message = f'🚫 Limite atteinte : {quota.trips_created}/3 voyages. Passez à Premium pour des voyages illimités !'
            
            elif quota_type == 'group':
                can_proceed = quota.can_join_group()
                error_message = f'🚫 Limite atteinte : {quota.groups_joined}/2 groupes. Passez à Premium pour rejoindre des groupes illimités !'
            
            elif quota_type == 'event':
                can_proceed = quota.can_create_event()
                error_message = f'🚫 Limite atteinte : {quota.events_created_this_month}/1 événement ce mois. Passez à Premium pour créer des événements illimités !'
            
            if not can_proceed:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': error_message,
                        'upgrade_url': '/upgrade/'
                    }, status=403)
                else:
                    messages.warning(request, error_message)
                    return redirect('upgrade')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def increment_quota(quota_type):
    """
    Décorateur pour incrémenter automatiquement un quota après une action réussie
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Exécuter la vue
            response = view_func(request, *args, **kwargs)
            
            # Si la réponse est un succès et que l'utilisateur est gratuit, incrémenter
            if request.user.is_authenticated and not request.user.subscription.is_premium:
                quota = request.user.quota
                
                if quota_type == 'post':
                    quota.posts_this_month += 1
                elif quota_type == 'message':
                    quota.messages_this_month += 1
                elif quota_type == 'trip':
                    quota.trips_created += 1
                elif quota_type == 'group':
                    quota.groups_joined += 1
                elif quota_type == 'event':
                    quota.events_created_this_month += 1
                
                quota.save()
            
            return response
        return wrapper
    return decorator