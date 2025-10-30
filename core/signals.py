from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Subscription, UsageQuota, PaymentHistory
from django.utils import timezone


@receiver(post_save, sender=User)
def create_user_subscription_and_quota(sender, instance, created, **kwargs):
    """
    Crée automatiquement un abonnement FREE et un quota 
    quand un nouvel utilisateur est créé
    """
    if created:
        # Créer l'abonnement FREE par défaut
        Subscription.objects.get_or_create(
            user=instance,
            defaults={
                'plan': 'FREE',
                'is_active': True,
                'payment_method': 'MANUAL'
            }
        )
        
        # Créer le quota
        UsageQuota.objects.get_or_create(
            user=instance,
            defaults={
                'posts_this_month': 0,
                'messages_this_month': 0,
                'events_created_this_month': 0,
                'trips_created': 0,
                'groups_joined': 0
            }
        )
        
        print(f"✅ [SIGNAL] Abonnement FREE et quota créés pour {instance.username}")


@receiver(post_save, sender=PaymentHistory)
def update_subscription_on_payment_completion(sender, instance, created, **kwargs):
    """
    SIGNAL CRITIQUE : Met à jour l'abonnement automatiquement 
    quand un paiement passe à COMPLETED
    
    Déclencheurs :
    - Admin marque un paiement comme COMPLETED
    - Webhook Stripe confirme un paiement
    - Paiement Flouci confirmé
    """
    # Vérifier si le paiement vient d'être marqué comme COMPLETED
    if instance.status == 'COMPLETED' and instance.subscription:
        subscription = instance.subscription
        
        print(f"🔄 [SIGNAL] Mise à jour de l'abonnement pour {subscription.user.username}")
        print(f"   Plan acheté: {instance.plan_purchased}")
        print(f"   Durée: {instance.duration_months} mois")
        
        # Mettre à jour l'abonnement selon le plan acheté
        if instance.plan_purchased == 'PREMIUM':
            subscription.upgrade_to_premium(
                duration_months=instance.duration_months,
                payment_method=instance.payment_method
            )
            print(f"✅ [SIGNAL] Abonnement PREMIUM activé jusqu'au {subscription.end_date}")
            
        elif instance.plan_purchased == 'BUSINESS':
            subscription.upgrade_to_business(
                duration_months=instance.duration_months,
                payment_method=instance.payment_method
            )
            print(f"✅ [SIGNAL] Abonnement BUSINESS activé jusqu'au {subscription.end_date}")
        
        # Enregistrer le montant payé dans l'abonnement
        subscription.amount_paid = instance.amount
        subscription.currency = instance.currency
        subscription.save()
        
        print(f"💰 [SIGNAL] Montant enregistré: {instance.amount} {instance.currency}")


@receiver(pre_save, sender=Subscription)
def check_subscription_expiration(sender, instance, **kwargs):
    """
    Vérifie automatiquement si un abonnement a expiré 
    avant chaque sauvegarde
    
    Si expiré et pas de renouvellement auto → retour à FREE
    """
    if instance.pk:  # Si l'abonnement existe déjà
        if instance.is_expired and not instance.auto_renew:
            if instance.plan != 'FREE':
                print(f"⚠️ [SIGNAL] Abonnement expiré pour {instance.user.username}")
                print(f"   Retour au plan FREE")
                
                instance.plan = 'FREE'
                instance.is_active = True
                instance.end_date = None
                instance.auto_renew = False


@receiver(post_save, sender=UsageQuota)
def auto_reset_monthly_quotas_if_needed(sender, instance, **kwargs):
    """
    Réinitialise automatiquement les quotas mensuels 
    si le dernier reset date de plus d'un mois
    """
    from dateutil.relativedelta import relativedelta
    
    now = timezone.now()
    last_reset = instance.last_reset
    
    # Si le dernier reset date de plus d'un mois
    if now >= last_reset + relativedelta(months=1):
        print(f"🔄 [SIGNAL] Réinitialisation des quotas mensuels pour {instance.user.username}")
        instance.reset_monthly_quotas()


# ============================================
# SIGNAL POUR LOGS ET DEBUG
# ============================================

@receiver(post_save, sender=Subscription)
def log_subscription_changes(sender, instance, created, **kwargs):
    """
    Log tous les changements d'abonnement pour debug
    """
    if created:
        print(f"📝 [LOG] Nouvel abonnement créé: {instance.user.username} - {instance.plan}")
    else:
        print(f"📝 [LOG] Abonnement mis à jour: {instance.user.username} - {instance.plan}")
        if instance.end_date:
            print(f"   Expire le: {instance.end_date.strftime('%d/%m/%Y %H:%M')}")