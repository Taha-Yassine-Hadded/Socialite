from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import (
    UserProfile, Post, Comment, Reaction, Share, Avis,
    Subscription, UsageQuota, PaymentHistory
)

# ============================================
# ADMIN ABONNEMENTS AMÉLIORÉ
# ============================================

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan_badge', 'status_badge', 'start_date', 'end_date', 
                    'payment_method', 'auto_renew', 'time_left']
    list_filter = ['plan', 'is_active', 'payment_method', 'auto_renew']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'start_date']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Abonnement', {
            'fields': ('plan', 'is_active', 'auto_renew')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'trial_end_date')
        }),
        ('Paiement', {
            'fields': ('payment_method', 'amount_paid', 'currency', 
                      'stripe_subscription_id', 'stripe_customer_id')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def plan_badge(self, obj):
        colors = {
            'FREE': '#6b7280',
            'PREMIUM': '#f59e0b',
            'BUSINESS': '#3b82f6'
        }
        icons = {
            'FREE': '🆓',
            'PREMIUM': '⭐',
            'BUSINESS': '🏢'
        }
        color = colors.get(obj.plan, '#000')
        icon = icons.get(obj.plan, '')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_plan_display()
        )
    plan_badge.short_description = 'Plan'
    
    def status_badge(self, obj):
        if obj.is_expired:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 5px 10px; border-radius: 5px;">⚠️ Expiré</span>'
            )
        elif obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 5px 10px; border-radius: 5px;">✅ Actif</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #6b7280; color: white; padding: 5px 10px; border-radius: 5px;">❌ Inactif</span>'
            )
    status_badge.short_description = 'Statut'
    
    def time_left(self, obj):
        if not obj.end_date:
            return '∞ Illimité'
        
        from django.utils import timezone
        delta = obj.end_date - timezone.now()
        
        if delta.days < 0:
            return format_html('<span style="color: red;">Expiré depuis {} jours</span>', abs(delta.days))
        elif delta.days == 0:
            return format_html('<span style="color: orange;">⚠️ Expire aujourd\'hui</span>')
        elif delta.days < 7:
            return format_html('<span style="color: orange;">⚠️ {} jours restants</span>', delta.days)
        else:
            return f'{delta.days} jours restants'
    time_left.short_description = 'Temps restant'
    
    actions = ['upgrade_to_premium_1m', 'upgrade_to_premium_12m', 
               'upgrade_to_business_1m', 'upgrade_to_business_12m',
               'downgrade_to_free', 'cancel_subscription', 'extend_subscription']
    
    def upgrade_to_premium_1m(self, request, queryset):
        count = 0
        for subscription in queryset:
            subscription.upgrade_to_premium(duration_months=1, payment_method='MANUAL')
            count += 1
        self.message_user(request, f'✅ {count} abonnement(s) passé(s) à Premium (1 mois)', messages.SUCCESS)
    upgrade_to_premium_1m.short_description = '⭐ Premium 1 mois'
    
    def upgrade_to_premium_12m(self, request, queryset):
        count = 0
        for subscription in queryset:
            subscription.upgrade_to_premium(duration_months=12, payment_method='MANUAL')
            count += 1
        self.message_user(request, f'✅ {count} abonnement(s) passé(s) à Premium (12 mois)', messages.SUCCESS)
    upgrade_to_premium_12m.short_description = '⭐ Premium 12 mois'
    
    def upgrade_to_business_1m(self, request, queryset):
        count = 0
        for subscription in queryset:
            subscription.upgrade_to_business(duration_months=1, payment_method='MANUAL')
            count += 1
        self.message_user(request, f'✅ {count} abonnement(s) passé(s) à Business (1 mois)', messages.SUCCESS)
    upgrade_to_business_1m.short_description = '🏢 Business 1 mois'
    
    def upgrade_to_business_12m(self, request, queryset):
        count = 0
        for subscription in queryset:
            subscription.upgrade_to_business(duration_months=12, payment_method='MANUAL')
            count += 1
        self.message_user(request, f'✅ {count} abonnement(s) passé(s) à Business (12 mois)', messages.SUCCESS)
    upgrade_to_business_12m.short_description = '🏢 Business 12 mois'
    
    def downgrade_to_free(self, request, queryset):
        count = 0
        for subscription in queryset:
            subscription.downgrade_to_free()
            count += 1
        self.message_user(request, f'✅ {count} abonnement(s) repassé(s) à Free', messages.SUCCESS)
    downgrade_to_free.short_description = '🆓 Repasser à Free'
    
    def cancel_subscription(self, request, queryset):
        count = 0
        for subscription in queryset:
            subscription.cancel()
            count += 1
        self.message_user(request, f'✅ {count} renouvellement(s) annulé(s)', messages.WARNING)
    cancel_subscription.short_description = '❌ Annuler le renouvellement'
    
    def extend_subscription(self, request, queryset):
        from dateutil.relativedelta import relativedelta
        count = 0
        for subscription in queryset:
            if subscription.end_date:
                subscription.end_date = subscription.end_date + relativedelta(months=1)
                subscription.save()
                count += 1
        self.message_user(request, f'✅ {count} abonnement(s) prolongé(s) d\'1 mois', messages.SUCCESS)
    extend_subscription.short_description = '⏱️ Prolonger de 1 mois'


@admin.register(UsageQuota)
class UsageQuotaAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscription_type', 'posts_usage', 'messages_usage', 
                    'trips_usage', 'groups_usage', 'events_usage', 'last_reset']
    list_filter = ['last_reset', 'user__subscription__plan']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'last_reset']
    
    def subscription_type(self, obj):
        plan = obj.user.subscription.plan
        colors = {'FREE': '#6b7280', 'PREMIUM': '#f59e0b', 'BUSINESS': '#3b82f6'}
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(plan, '#000'), plan
        )
    subscription_type.short_description = 'Plan'
    
    def posts_usage(self, obj):
        if obj.user.subscription.is_premium:
            return '∞ Illimité'
        return f'{obj.posts_this_month}/10'
    posts_usage.short_description = 'Posts'
    
    def messages_usage(self, obj):
        if obj.user.subscription.is_premium:
            return '∞ Illimité'
        return f'{obj.messages_this_month}/50'
    messages_usage.short_description = 'Messages'
    
    def trips_usage(self, obj):
        if obj.user.subscription.is_premium:
            return '∞ Illimité'
        return f'{obj.trips_created}/3'
    trips_usage.short_description = 'Voyages'
    
    def groups_usage(self, obj):
        if obj.user.subscription.is_premium:
            return '∞ Illimité'
        return f'{obj.groups_joined}/2'
    groups_usage.short_description = 'Groupes'
    
    def events_usage(self, obj):
        if obj.user.subscription.is_premium:
            return '∞ Illimité'
        return f'{obj.events_created_this_month}/1'
    events_usage.short_description = 'Événements'
    
    actions = ['reset_monthly_quotas', 'reset_all_quotas']
    
    def reset_monthly_quotas(self, request, queryset):
        count = 0
        for quota in queryset:
            quota.reset_monthly_quotas()
            count += 1
        self.message_user(request, f'✅ {count} quota(s) mensuel(s) réinitialisé(s)', messages.SUCCESS)
    reset_monthly_quotas.short_description = '🔄 Réinitialiser quotas mensuels'
    
    def reset_all_quotas(self, request, queryset):
        count = 0
        for quota in queryset:
            quota.posts_this_month = 0
            quota.messages_this_month = 0
            quota.events_created_this_month = 0
            quota.trips_created = 0
            quota.groups_joined = 0
            quota.save()
            count += 1
        self.message_user(request, f'✅ {count} quota(s) complètement réinitialisé(s)', messages.WARNING)
    reset_all_quotas.short_description = '🔄 RESET COMPLET (tous les quotas)'


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount_display', 'plan_badge', 'duration_display', 
                    'status_badge', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'plan_purchased', 'created_at']
    search_fields = ['user__username', 'user__email', 'stripe_payment_intent_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user', 'subscription')
        }),
        ('Paiement', {
            'fields': ('amount', 'currency', 'status', 'payment_method')
        }),
        ('Plan', {
            'fields': ('plan_purchased', 'duration_months')
        }),
        ('IDs externes', {
            'fields': ('stripe_payment_intent_id', 'invoice_url')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def amount_display(self, obj):
        return format_html(
            '<strong style="color: #10b981;">{} {}</strong>',
            obj.amount, obj.currency
        )
    amount_display.short_description = 'Montant'
    
    def plan_badge(self, obj):
        colors = {'PREMIUM': '#f59e0b', 'BUSINESS': '#3b82f6'}
        icons = {'PREMIUM': '⭐', 'BUSINESS': '🏢'}
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{} {}</span>',
            colors.get(obj.plan_purchased, '#000'),
            icons.get(obj.plan_purchased, ''),
            obj.plan_purchased
        )
    plan_badge.short_description = 'Plan'
    
    def duration_display(self, obj):
        if obj.duration_months == 1:
            return '1️⃣ 1 mois'
        elif obj.duration_months == 12:
            return '🔢 12 mois'
        else:
            return f'{obj.duration_months} mois'
    duration_display.short_description = 'Durée'
    
    def status_badge(self, obj):
        colors = {
            'PENDING': '#f59e0b',
            'COMPLETED': '#10b981',
            'FAILED': '#ef4444',
            'REFUNDED': '#6b7280'
        }
        icons = {
            'PENDING': '⏳',
            'COMPLETED': '✅',
            'FAILED': '❌',
            'REFUNDED': '💸'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{} {}</span>',
            colors.get(obj.status, '#000'),
            icons.get(obj.status, ''),
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    actions = ['mark_as_completed', 'mark_as_failed', 'mark_as_refunded']
    
    def mark_as_completed(self, request, queryset):
        """
        ⚠️ ACTION CRITIQUE : Marquer un paiement comme COMPLÉTÉ
        Cela déclenche automatiquement la mise à jour de l'abonnement via SIGNAL
        """
        count = 0
        for payment in queryset:
            if payment.status != 'COMPLETED':
                payment.status = 'COMPLETED'
                payment.save()  # Le signal update_subscription_on_payment_completion sera déclenché
                count += 1
        
        self.message_user(
            request, 
            f'✅ {count} paiement(s) marqué(s) comme COMPLÉTÉ. Les abonnements ont été mis à jour automatiquement !',
            messages.SUCCESS
        )
    mark_as_completed.short_description = '✅ Marquer comme COMPLÉTÉ (active l\'abonnement)'
    
    def mark_as_failed(self, request, queryset):
        count = queryset.update(status='FAILED')
        self.message_user(request, f'❌ {count} paiement(s) marqué(s) comme ÉCHOUÉ', messages.ERROR)
    mark_as_failed.short_description = '❌ Marquer comme ÉCHOUÉ'
    
    def mark_as_refunded(self, request, queryset):
        count = queryset.update(status='REFUNDED')
        self.message_user(request, f'💸 {count} paiement(s) marqué(s) comme REMBOURSÉ', messages.WARNING)
    mark_as_refunded.short_description = '💸 Marquer comme REMBOURSÉ'


# ============================================
# ADMIN EXISTANTS (inchangés)
# ============================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'slug', 'location', 'travel_style', 'created_at']
    search_fields = ['user__username', 'user__email', 'slug']
    list_filter = ['travel_style', 'created_at']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_preview', 'visibility', 'likes_count', 'comments_count', 'created_at']
    list_filter = ['visibility', 'created_at']
    search_fields = ['user__username', 'content']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if obj.content and len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Contenu'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'content_preview', 'parent', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'content']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Contenu'


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'reaction_type', 'post', 'comment', 'created_at']
    list_filter = ['reaction_type', 'created_at']
    search_fields = ['user__username']


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ['user', 'original_post', 'message_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'message']
    
    def message_preview(self, obj):
        if not obj.message:
            return '(Aucun message)'
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'


@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = ['reviewer', 'reviewee', 'note', 'communication', 'fiabilite', 'sympathie', 'created_at']
    list_filter = ['note', 'created_at']
    search_fields = ['reviewer__username', 'reviewee__username']