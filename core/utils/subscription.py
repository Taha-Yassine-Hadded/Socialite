# core/utils/subscription.py
from django.conf import settings
from core.models import Subscription, UsageQuota

def get_subscription_limit(user, limit_name):
    """
    Récupère la limite pour un utilisateur selon son plan.
    
    Args:
        user: L'utilisateur Django
        limit_name: Nom de la limite (ex: 'posts_per_month')
    
    Returns:
        int: La limite (-1 si illimitée)
    """
    try:
        subscription = user.subscription
        plan = subscription.plan
    except Subscription.DoesNotExist:
        plan = 'FREE'
    
    limits = settings.SUBSCRIPTION_LIMITS.get(plan, settings.SUBSCRIPTION_LIMITS['FREE'])
    return limits.get(limit_name, 0)


def can_user_perform_action(user, action_type):
    """
    Vérifie si un utilisateur peut effectuer une action.
    
    Args:
        user: L'utilisateur Django
        action_type: Type d'action ('post', 'message', 'trip', 'group', 'event')
    
    Returns:
        tuple: (bool, str) - (Peut effectuer l'action, Message d'erreur)
    """
    try:
        subscription = user.subscription
    except Subscription.DoesNotExist:
        subscription, _ = Subscription.objects.get_or_create(
            user=user,
            defaults={
                'plan': 'FREE',
                'is_active': True,
                'payment_method': 'MANUAL',
            },
        )
    try:
        quota = user.quota
    except UsageQuota.DoesNotExist:
        quota, _ = UsageQuota.objects.get_or_create(
            user=user,
            defaults={
                'posts_this_month': 0,
                'messages_this_month': 0,
                'events_created_this_month': 0,
                'trips_created': 0,
                'groups_joined': 0,
            },
        )
    
    # Si l'utilisateur est Premium ou Business, tout est permis
    if subscription.is_premium:
        return True, ""
    
    # Vérifications pour FREE
    if action_type == 'post':
        limit = get_subscription_limit(user, 'posts_per_month')
        if quota.posts_this_month >= limit:
            return False, f"Limite atteinte : {limit} posts/mois. Passez à Premium pour des posts illimités !"
    
    elif action_type == 'message':
        limit = get_subscription_limit(user, 'messages_per_month')
        if quota.messages_this_month >= limit:
            return False, f"Limite atteinte : {limit} messages/mois. Passez à Premium !"
    
    elif action_type == 'trip':
        limit = get_subscription_limit(user, 'trips_max')
        if quota.trips_created >= limit:
            return False, f"Limite atteinte : {limit} voyages maximum. Passez à Premium !"
    
    elif action_type == 'group':
        limit = get_subscription_limit(user, 'groups_max')
        if quota.groups_joined >= limit:
            return False, f"Limite atteinte : {limit} groupes maximum. Passez à Premium !"
    
    elif action_type == 'event':
        limit = get_subscription_limit(user, 'events_per_month')
        if quota.events_created_this_month >= limit:
            return False, f"Limite atteinte : {limit} événement/mois. Passez à Premium !"
    
    return True, ""


def increment_usage(user, action_type):
    """
    Incrémenter le compteur d'utilisation.
    
    Args:
        user: L'utilisateur Django
        action_type: Type d'action ('post', 'message', 'trip', 'group', 'event')
    """
    try:
        quota = user.quota
    except UsageQuota.DoesNotExist:
        quota, _ = UsageQuota.objects.get_or_create(
            user=user,
            defaults={
                'posts_this_month': 0,
                'messages_this_month': 0,
                'events_created_this_month': 0,
                'trips_created': 0,
                'groups_joined': 0,
            },
        )
    
    if action_type == 'post':
        quota.posts_this_month += 1
    elif action_type == 'message':
        quota.messages_this_month += 1
    elif action_type == 'trip':
        quota.trips_created += 1
    elif action_type == 'group':
        quota.groups_joined += 1
    elif action_type == 'event':
        quota.events_created_this_month += 1
    
    quota.save()