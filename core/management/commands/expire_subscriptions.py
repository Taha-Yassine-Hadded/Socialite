from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Subscription, UsageQuota
from dateutil.relativedelta import relativedelta


class Command(BaseCommand):
    help = 'Vérifie et expire les abonnements + réinitialise les quotas mensuels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Afficher ce qui serait fait sans appliquer les changements',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        
        self.stdout.write(self.style.SUCCESS(f'\n🔍 Vérification des abonnements - {now.strftime("%d/%m/%Y %H:%M")}'))
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️ MODE DRY-RUN : Aucune modification ne sera appliquée\n'))
        
        # ============================================
        # 1. EXPIRER LES ABONNEMENTS
        # ============================================
        
        expired_subscriptions = Subscription.objects.filter(
            end_date__lte=now,
            is_active=True,
            auto_renew=False
        ).exclude(plan='FREE')
        
        expired_count = expired_subscriptions.count()
        
        if expired_count > 0:
            self.stdout.write(f'\n📉 {expired_count} abonnement(s) expiré(s) trouvé(s):')
            
            for subscription in expired_subscriptions:
                self.stdout.write(
                    f'   - {subscription.user.username} ({subscription.plan}) - Expiré depuis {(now - subscription.end_date).days} jours'
                )
                
                if not dry_run:
                    # Retour au plan FREE
                    subscription.downgrade_to_free()
                    self.stdout.write(self.style.SUCCESS(f'      ✅ Repassé à FREE'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Aucun abonnement expiré'))
        
        # ============================================
        # 2. RENOUVELER LES ABONNEMENTS AUTO
        # ============================================
        
        auto_renew_subscriptions = Subscription.objects.filter(
            end_date__lte=now,
            is_active=True,
            auto_renew=True
        ).exclude(plan='FREE')
        
        auto_renew_count = auto_renew_subscriptions.count()
        
        if auto_renew_count > 0:
            self.stdout.write(f'\n🔄 {auto_renew_count} abonnement(s) à renouveler automatiquement:')
            
            for subscription in auto_renew_subscriptions:
                self.stdout.write(
                    f'   - {subscription.user.username} ({subscription.plan})'
                )
                
                if not dry_run:
                    # Prolonger de 1 mois (ou gérer le paiement automatique ici)
                    subscription.end_date = subscription.end_date + relativedelta(months=1)
                    subscription.save()
                    self.stdout.write(self.style.SUCCESS(
                        f'      ✅ Prolongé jusqu\'au {subscription.end_date.strftime("%d/%m/%Y")}'
                    ))
                    
                    # TODO: Déclencher le paiement automatique via Stripe/Flouci
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Aucun abonnement à renouveler'))
        
        # ============================================
        # 3. RÉINITIALISER LES QUOTAS MENSUELS
        # ============================================
        
        quotas_to_reset = UsageQuota.objects.filter(
            last_reset__lte=now - relativedelta(months=1)
        )
        
        quotas_count = quotas_to_reset.count()
        
        if quotas_count > 0:
            self.stdout.write(f'\n🔄 {quotas_count} quota(s) à réinitialiser:')
            
            for quota in quotas_to_reset:
                self.stdout.write(
                    f'   - {quota.user.username} (dernier reset: {quota.last_reset.strftime("%d/%m/%Y")})'
                )
                
                if not dry_run:
                    quota.reset_monthly_quotas()
                    self.stdout.write(self.style.SUCCESS('      ✅ Quotas mensuels réinitialisés'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Aucun quota à réinitialiser'))
        
        # ============================================
        # 4. STATISTIQUES FINALES
        # ============================================
        
        total_subscriptions = Subscription.objects.count()
        free_count = Subscription.objects.filter(plan='FREE').count()
        premium_count = Subscription.objects.filter(plan='PREMIUM', is_active=True).count()
        business_count = Subscription.objects.filter(plan='BUSINESS', is_active=True).count()
        
        self.stdout.write(f'\n📊 STATISTIQUES:')
        self.stdout.write(f'   Total abonnements: {total_subscriptions}')
        self.stdout.write(f'   🆓 FREE: {free_count}')
        self.stdout.write(f'   ⭐ PREMIUM: {premium_count}')
        self.stdout.write(f'   🏢 BUSINESS: {business_count}')
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Tâche terminée avec succès\n'))
        else:
            self.stdout.write(self.style.WARNING(f'\n⚠️ DRY-RUN terminé - Aucune modification appliquée\n'))