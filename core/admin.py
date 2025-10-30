from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UserProfile, Post, Comment, Reaction, Share, Avis,
    Subscription, UsageQuota, PaymentHistory
)

# ============================================
# ADMIN ABONNEMENTS
# ============================================

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan_badge', 'is_active', 'start_date', 'end_date', 'payment_method', 'auto_renew']
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
    
    actions = ['upgrade_to_premium', 'upgrade_to_business', 'downgrade_to_free', 'cancel_subscription']
    
    def upgrade_to_premium(self, request, queryset):
        for subscription in queryset:
            subscription.upgrade_to_premium(duration_months=1, payment_method='MANUAL')
        self.message_user(request, f'{queryset.count()} abonnements passés à Premium')
    upgrade_to_premium.short_description = '⭐ Passer à Premium (1 mois)'
    
    def upgrade_to_business(self, request, queryset):
        for subscription in queryset:
            subscription.upgrade_to_business(duration_months=1, payment_method='MANUAL')
        self.message_user(request, f'{queryset.count()} abonnements passés à Business')
    upgrade_to_business.short_description = '🏢 Passer à Business (1 mois)'
    
    def downgrade_to_free(self, request, queryset):
        for subscription in queryset:
            subscription.downgrade_to_free()
        self.message_user(request, f'{queryset.count()} abonnements passés à Free')
    downgrade_to_free.short_description = '🆓 Repasser à Free'
    
    def cancel_subscription(self, request, queryset):
        for subscription in queryset:
            subscription.cancel()
        self.message_user(request, f'{queryset.count()} abonnements annulés')
    cancel_subscription.short_description = '❌ Annuler le renouvellement'


@admin.register(UsageQuota)
class UsageQuotaAdmin(admin.ModelAdmin):
    list_display = ['user', 'posts_this_month', 'messages_this_month', 'trips_created', 
                    'groups_joined', 'events_created_this_month', 'last_reset']
    list_filter = ['last_reset']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'last_reset']
    
    actions = ['reset_monthly_quotas']
    
    def reset_monthly_quotas(self, request, queryset):
        for quota in queryset:
            quota.reset_monthly_quotas()
        self.message_user(request, f'{queryset.count()} quotas mensuels réinitialisés')
    reset_monthly_quotas.short_description = '🔄 Réinitialiser les quotas mensuels'


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount_display', 'plan_purchased', 'status_badge', 
                    'payment_method', 'created_at']
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
            'fields': ('stripe_payment_intent_id',  'invoice_url')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def amount_display(self, obj):
        return f'{obj.amount} {obj.currency}'
    amount_display.short_description = 'Montant'
    
    def status_badge(self, obj):
        colors = {
            'PENDING': '#f59e0b',
            'COMPLETED': '#10b981',
            'FAILED': '#ef4444',
            'REFUNDED': '#6b7280'
        }
        color = colors.get(obj.status, '#000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'


# ============================================
# ADMIN EXISTANTS (à garder)
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