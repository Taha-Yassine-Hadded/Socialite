from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from dateutil.relativedelta import relativedelta


# ============================================
# PROFIL UTILISATEUR
# ============================================

class UserProfile(models.Model):
    # Lien avec l'utilisateur Django
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Slug unique pour l'URL du profil (ex: hiba-louhibi)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True, help_text="URL unique du profil (ex: hiba-louhibi)")
    
    # Informations de base
    bio = models.TextField(max_length=500, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    
    # Photo de profil et couverture
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    
    # Réseaux sociaux
    website = models.URLField(max_length=200, blank=True, null=True)
    facebook = models.CharField(max_length=100, blank=True, null=True)
    instagram = models.CharField(max_length=100, blank=True, null=True)
    twitter = models.CharField(max_length=100, blank=True, null=True)
    
    # Préférences voyage
    favorite_destinations = models.TextField(blank=True, null=True)
    travel_style = models.CharField(max_length=50, choices=[
        ('aventure', 'Aventure'),
        ('luxe', 'Luxe'),
        ('backpacker', 'Backpacker'),
        ('famille', 'Famille'),
        ('solo', 'Solo'),
    ], blank=True, null=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """
        Générer automatiquement le slug lors de la sauvegarde
        Format: prenom-nom (ex: hiba-louhibi)
        """
        if not self.slug:
            # Générer le slug basé sur prénom et nom
            base_slug = slugify(f"{self.user.first_name}-{self.user.last_name}".lower())
            
            # Si le slug est vide (pas de nom/prénom), utiliser l'ID de l'utilisateur
            if not base_slug or base_slug == '-':
                base_slug = f"user-{self.user.id}"
            
            # Vérifier l'unicité et ajouter un numéro si nécessaire
            slug = base_slug
            counter = 1
            while UserProfile.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Profil de {self.user.username}"


# ============================================
# SYSTÈME D'ABONNEMENT
# ============================================

class Subscription(models.Model):
    """
    Gestion des abonnements utilisateurs (FREE, PREMIUM, BUSINESS)
    """
    PLAN_CHOICES = [
        ('FREE', 'Gratuit'),
        ('PREMIUM', 'Premium'),
        ('BUSINESS', 'Business'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('STRIPE', 'Stripe (International)'),
        
        ('MANUAL', 'Manuel (Admin)'),
    ]
    
    # Relations
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    
    # Plan et statut
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='FREE')
    is_active = models.BooleanField(default=True)
    
    # Dates
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    trial_end_date = models.DateTimeField(null=True, blank=True)
    
    # Paiement
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='STRIPE')
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)

    
    # Prix payé (pour historique)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='EUR')
    
    # Auto-renouvellement
    auto_renew = models.BooleanField(default=True)
    
    # Dates de suivi
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Abonnement'
        verbose_name_plural = 'Abonnements'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_plan_display()}"
    
    @property
    def is_premium(self):
        """Vérifie si l'utilisateur a Premium ou Business"""
        return self.plan in ['PREMIUM', 'BUSINESS'] and self.is_active
    
    @property
    def is_business(self):
        """Vérifie si l'utilisateur a Business"""
        return self.plan == 'BUSINESS' and self.is_active
    
    @property
    def is_expired(self):
        """Vérifie si l'abonnement a expiré"""
        if not self.end_date:
            return False
        return timezone.now() > self.end_date
    
    def cancel(self):
        """Annuler l'abonnement"""
        self.auto_renew = False
        self.save()
    
    def upgrade_to_premium(self, duration_months=1, payment_method='STRIPE'):
        """Passer à Premium"""
        self.plan = 'PREMIUM'
        self.is_active = True
        self.payment_method = payment_method
        self.start_date = timezone.now()
        self.end_date = timezone.now() + relativedelta(months=duration_months)
        self.save()
    
    def upgrade_to_business(self, duration_months=1, payment_method='STRIPE'):
        """Passer à Business"""
        self.plan = 'BUSINESS'
        self.is_active = True
        self.payment_method = payment_method
        self.start_date = timezone.now()
        self.end_date = timezone.now() + relativedelta(months=duration_months)
        self.save()
    
    def downgrade_to_free(self):
        """Retourner à Free"""
        self.plan = 'FREE'
        self.is_active = True
        self.end_date = None
        self.auto_renew = False
        self.save()


class UsageQuota(models.Model):
    """
    Suivi des quotas d'utilisation pour les comptes gratuits
    """
    # Relations
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='quota')
    
    # Compteurs mensuels (reset chaque mois)
    posts_this_month = models.IntegerField(default=0)
    messages_this_month = models.IntegerField(default=0)
    events_created_this_month = models.IntegerField(default=0)
    
    # Compteurs permanents
    trips_created = models.IntegerField(default=0)
    groups_joined = models.IntegerField(default=0)
    
    # Date de dernier reset
    last_reset = models.DateTimeField(auto_now_add=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Quota d\'utilisation'
        verbose_name_plural = 'Quotas d\'utilisation'
    
    def __str__(self):
        return f"Quota de {self.user.username}"
    
    def reset_monthly_quotas(self):
        """Réinitialiser les compteurs mensuels"""
        self.posts_this_month = 0
        self.messages_this_month = 0
        self.events_created_this_month = 0
        self.last_reset = timezone.now()
        self.save()
    
    def can_create_post(self):
        """Vérifier si l'utilisateur peut créer un post"""
        if self.user.subscription.is_premium:
            return True
        return self.posts_this_month < 10
    
    def can_send_message(self):
        """Vérifier si l'utilisateur peut envoyer un message"""
        if self.user.subscription.is_premium:
            return True
        return self.messages_this_month < 50
    
    def can_create_trip(self):
        """Vérifier si l'utilisateur peut créer un voyage"""
        if self.user.subscription.is_premium:
            return True
        return self.trips_created < 3
    
    def can_join_group(self):
        """Vérifier si l'utilisateur peut rejoindre un groupe"""
        if self.user.subscription.is_premium:
            return True
        return self.groups_joined < 2
    
    def can_create_event(self):
        """Vérifier si l'utilisateur peut créer un événement"""
        if self.user.subscription.is_premium:
            return True
        return self.events_created_this_month < 1


class PaymentHistory(models.Model):
    """
    Historique des paiements
    """
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('COMPLETED', 'Complété'),
        ('FAILED', 'Échoué'),
        ('REFUNDED', 'Remboursé'),
    ]
    
    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True)
    
    # Détails du paiement
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # IDs externes
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    
    
    # Plan acheté
    plan_purchased = models.CharField(max_length=20)
    duration_months = models.IntegerField(default=1)
    
    # Métadonnées
    payment_method = models.CharField(max_length=20)
    invoice_url = models.URLField(blank=True, null=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Historique de paiement'
        verbose_name_plural = 'Historiques de paiements'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.amount}{self.currency} - {self.get_status_display()}"


# ============================================
# SYSTÈME DE POSTS
# ============================================

class Post(models.Model):
    """
    Modèle pour les publications (posts) des utilisateurs.
    Supporte : texte, images, vidéos, notes vocales
    """
    # Relation avec l'utilisateur qui a créé le post
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    
    # Contenu du post
    content = models.TextField(blank=True, null=True, help_text="Texte du post")
    
    # Fichiers multimédias (optionnels)
    image = models.ImageField(upload_to='posts/images/', blank=True, null=True, help_text="Photo du post")
    video = models.FileField(upload_to='posts/videos/', blank=True, null=True, help_text="Vidéo du post")
    voice_note = models.FileField(upload_to='posts/voice_notes/', blank=True, null=True, help_text="Note vocale")
    
    # IA - Transcription automatique de la note vocale (Whisper)
    voice_transcription = models.TextField(blank=True, null=True, help_text="Transcription automatique de la note vocale")
    detected_language = models.CharField(max_length=10, blank=True, null=True, help_text="Langue détectée (ex: fr, ar, en)")
    
    # IA - Classification automatique d'images de voyage (ResNet18)
    image_category = models.CharField(max_length=50, blank=True, null=True, help_text="Catégorie détectée (beach, mountain, city, etc.)")
    image_category_fr = models.CharField(max_length=50, blank=True, null=True, help_text="Catégorie en français")
    image_confidence = models.FloatField(blank=True, null=True, help_text="Confiance de la prédiction (0-1)")
    image_tags = models.JSONField(blank=True, null=True, help_text="Tags automatiques générés")
    
    # Métadonnées
    location = models.CharField(max_length=200, blank=True, null=True, help_text="Lieu du post")
    
    # Statistiques (dénormalisées pour performance)
    likes_count = models.IntegerField(default=0, help_text="Nombre de likes")
    comments_count = models.IntegerField(default=0, help_text="Nombre de commentaires")
    shares_count = models.IntegerField(default=0, help_text="Nombre de partages")
    
    # Visibilité du post
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('friends', 'Amis seulement'),
        ('private', 'Privé'),
    ]
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Post partagé (si c'est un partage d'un autre post)
    shared_post = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='shares')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Publication'
        verbose_name_plural = 'Publications'
    
    def __str__(self):
        return f"Post de {self.user.username} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"


class Comment(models.Model):
    """
    Modèle pour les commentaires sur les posts.
    Supporte les commentaires imbriqués (réponses aux commentaires).
    """
    # Relations
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    
    # Contenu du commentaire
    content = models.TextField(help_text="Texte du commentaire")
    
    # Commentaire parent (pour les réponses)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Image optionnelle dans le commentaire
    image = models.ImageField(upload_to='comments/images/', blank=True, null=True)
    
    # Statistiques
    likes_count = models.IntegerField(default=0)
    
    # Date
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'
    
    def __str__(self):
        return f"Commentaire de {self.user.username} sur post #{self.post.id}"


class Reaction(models.Model):
    """
    Modèle pour les réactions (likes, love, etc.) sur les posts et commentaires.
    Inspiré de Facebook : plusieurs types de réactions possibles.
    """
    # Type de réaction disponibles
    REACTION_TYPES = [
        ('like', '👍 J\'aime'),
        ('love', '❤️ J\'adore'),
        ('haha', '😂 Haha'),
        ('wow', '😮 Wow'),
        ('sad', '😢 Triste'),
        ('angry', '😠 Grrr'),
    ]
    
    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')
    
    # Réaction sur un post OU un commentaire
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='reactions')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='reactions')
    
    # Type de réaction
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES, default='like')
    
    # Date
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [
            ['user', 'post'],
            ['user', 'comment']
        ]
        verbose_name = 'Réaction'
        verbose_name_plural = 'Réactions'
    
    def __str__(self):
        if self.post:
            return f"{self.user.username} - {self.get_reaction_type_display()} sur post #{self.post.id}"
        else:
            return f"{self.user.username} - {self.get_reaction_type_display()} sur commentaire #{self.comment.id}"


class Share(models.Model):
    """
    Modèle pour le partage de posts.
    """
    # Utilisateur qui partage le post
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_posts')
    
    # Post original qui est partagé
    original_post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_shares')
    
    # Message optionnel lors du partage
    message = models.TextField(blank=True, null=True, help_text="Message d'accompagnement")
    
    # Date du partage
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Partage'
        verbose_name_plural = 'Partages'
    
    def __str__(self):
        return f"{self.user.username} a partagé le post #{self.original_post.id}"


# ============================================
# AVIS (REVIEWS)
# ============================================

class Avis(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avis_left')
    reviewee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avis_received')
    note = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    communication = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    fiabilite = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    sympathie = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    commentaire = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['reviewer', 'reviewee']
        ordering = ['-created_at']

    def clean(self):
        # No self-review
        if self.reviewer_id == self.reviewee_id:
            raise ValidationError('Vous ne pouvez pas laisser un avis sur vous-même.')

        # Check mutual follow via MongoDB
        try:
            from .mongo import get_db
            db = get_db()
            prof_reviewer = db.profiles.find_one({'user_id': self.reviewer_id}) or {}
            prof_reviewee = db.profiles.find_one({'user_id': self.reviewee_id}) or {}
            following_r = set(prof_reviewer.get('following', []))
            following_e = set(prof_reviewee.get('following', []))
            if (self.reviewee_id not in following_r) or (self.reviewer_id not in following_e):
                raise ValidationError("Un suivi mutuel est requis pour laisser un avis.")
        except Exception:
            raise ValidationError("Impossible de vérifier le suivi mutuel pour le moment.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Avis {self.reviewer.username} → {self.reviewee.username} ({self.note}/5)"


# ============================================
# ANALYTICS (IA & Engagement)
# ============================================
class AnalyticsEvent(models.Model):
    """
    Événements analytiques pour le tableau de bord IA et d'engagement.
    Permet d'agréger des métriques sans requêtes coûteuses en direct.
    """
    EVENT_TYPES = [
        ('create_post', 'Création de post'),
        ('view_feed', 'Vue du feed'),
        ('analyze_image', 'Analyse image (pré-upload)'),
        ('whisper_ok', 'Transcription réussie'),
        ('whisper_fail', 'Transcription échouée'),
        ('classify_ok', 'Classification image réussie'),
        ('classify_fail', 'Classification image échouée'),
    ]

    event_type = models.CharField(max_length=32, choices=EVENT_TYPES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='analytics_events')
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True, related_name='analytics_events')

    # Dimensions utiles
    media_type = models.CharField(max_length=16, blank=True, null=True, help_text="text|image|video|voice|mixed")
    image_category = models.CharField(max_length=50, blank=True, null=True)
    detected_language = models.CharField(max_length=10, blank=True, null=True)
    success = models.BooleanField(null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)

    # Contenu brut/extra (JSON libre)
    meta = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['image_category']),
            models.Index(fields=['detected_language']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"AnalyticsEvent[{self.event_type}] user={getattr(self.user, 'id', None)} post={getattr(self.post, 'id', None)}"


# ============================================
# STORIES (24h)
# ============================================
from django.utils import timezone

class Story(models.Model):
    """Story type Instagram/Facebook. Expire après 24h."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    content_text = models.CharField(max_length=300, blank=True, null=True)
    image = models.ImageField(upload_to='stories/images/', blank=True, null=True)
    video = models.FileField(upload_to='stories/videos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Story #{self.id} by {self.user.username}"

    @property
    def expires_at(self):
        return self.created_at + timezone.timedelta(hours=24)

    @property
    def is_active(self):
        return timezone.now() < self.expires_at


class StoryView(models.Model):
    """Qui a vu quelle story (pour stats/privacité)."""
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_views')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['story', 'viewer']
        ordering = ['-viewed_at']

    def __str__(self):
        return f"view {self.viewer.username} -> story {self.story_id}"
    

    # ============================================
# FONCTIONNALITÉS PREMIUM/BUSINESS
# ============================================

class Wallet(models.Model):
    """
    Portefeuille virtuel pour gérer les budgets de voyage (PREMIUM/BUSINESS uniquement)
    """
    CURRENCY_CHOICES = [
        ('EUR', 'Euro (€)'),
        ('USD', 'Dollar ($)'),
        ('GBP', 'Livre Sterling (£)'),
        ('TND', 'Dinar Tunisien (TND)'),
        ('MAD', 'Dirham Marocain (MAD)'),
    ]
    
    # Relations
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    
    # Informations financières
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, 
                                   help_text="Solde disponible")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='EUR')
    
    # Statistiques
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_saved = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Portefeuille'
        verbose_name_plural = 'Portefeuilles'
    
    def __str__(self):
        return f"Wallet de {self.user.username} - {self.balance} {self.currency}"
    
    def add_funds(self, amount):
        """Ajouter des fonds au portefeuille"""
        self.balance += amount
        self.total_saved += amount
        self.save()
    
    def withdraw_funds(self, amount):
        """Retirer des fonds du portefeuille"""
        if self.balance >= amount:
            self.balance -= amount
            self.total_spent += amount
            self.save()
            return True
        return False
    
    def get_balance_display(self):
        """Affichage formaté du solde"""
        symbols = {'EUR': '€', 'USD': '$', 'GBP': '£', 'TND': 'TND', 'MAD': 'MAD'}
        symbol = symbols.get(self.currency, self.currency)
        return f"{self.balance:.2f} {symbol}"


class WalletTransaction(models.Model):
    """
    Historique des transactions du portefeuille
    """
    TRANSACTION_TYPES = [
        ('DEPOSIT', '💰 Dépôt'),
        ('WITHDRAWAL', '💸 Retrait'),
        ('TRANSFER', '🔄 Transfert'),
        ('EXPENSE', '🛒 Dépense'),
    ]
    
    # Relations
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    
    # Détails de la transaction
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    
    # Lien optionnel vers un voyage ou événement
    related_trip = models.ForeignKey('Trip', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} - {self.created_at.strftime('%d/%m/%Y')}"


class BucketList(models.Model):
    """
    Liste de destinations de rêve (PREMIUM/BUSINESS uniquement)
    """
    STATUS_CHOICES = [
        ('PLANNED', '📅 Planifié'),
        ('IN_PROGRESS', '✈️ En cours'),
        ('COMPLETED', '✅ Visité'),
        ('CANCELLED', '❌ Annulé'),
    ]
    
    PRIORITY_CHOICES = [
        (1, '🔥 Très haute'),
        (2, '⭐ Haute'),
        (3, '📌 Moyenne'),
        (4, '💭 Basse'),
    ]
    
    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bucket_list')
    
    # Destination
    destination = models.CharField(max_length=200, help_text="Nom de la destination")
    country = models.CharField(max_length=100, help_text="Pays")
    city = models.CharField(max_length=100, blank=True, null=True)
    
    # Image de la destination
    image = models.ImageField(upload_to='bucket_list/', blank=True, null=True)
    
    # Détails
    description = models.TextField(blank=True, null=True, help_text="Pourquoi cette destination ?")
    estimated_budget = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, default='EUR')
    
    # Dates
    target_date = models.DateField(blank=True, null=True, help_text="Date souhaitée de visite")
    visited_date = models.DateField(blank=True, null=True, help_text="Date de visite réelle")
    
    # Statut et priorité
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=3)
    
    # Notes personnelles
    notes = models.TextField(blank=True, null=True)
    
    # IA - Tags générés automatiquement
    ai_tags = models.JSONField(blank=True, null=True, help_text="Tags générés par IA")
    ai_recommendations = models.TextField(blank=True, null=True, help_text="Recommandations IA")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Destination de rêve'
        verbose_name_plural = 'Bucket List'
        ordering = ['priority', '-created_at']
    
    def __str__(self):
        return f"{self.destination} ({self.country}) - {self.user.username}"
    
    def mark_as_visited(self):
        """Marquer comme visité"""
        self.status = 'COMPLETED'
        self.visited_date = timezone.now().date()
        self.save()
    
    def get_priority_display_icon(self):
        """Icône de priorité"""
        icons = {1: '🔥', 2: '⭐', 3: '📌', 4: '💭'}
        return icons.get(self.priority, '📌')


class Trip(models.Model):
    """
    Voyages planifiés (lien avec Wallet et BucketList)
    """
    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    bucket_list_item = models.ForeignKey(BucketList, on_delete=models.SET_NULL, 
                                          null=True, blank=True, 
                                          related_name='trips')
    
    # Détails du voyage
    title = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    # Dates
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Budget
    estimated_budget = models.DecimalField(max_digits=10, decimal_places=2)
    actual_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='EUR')
    
    # Participants
    participants = models.ManyToManyField(User, related_name='joined_trips', blank=True)
    
    # Statut
    STATUS_CHOICES = [
        ('PLANNING', 'En planification'),
        ('CONFIRMED', 'Confirmé'),
        ('ONGOING', 'En cours'),
        ('COMPLETED', 'Terminé'),
        ('CANCELLED', 'Annulé'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNING')
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Voyage'
        verbose_name_plural = 'Voyages'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.title} - {self.destination}"
    
    @property
    def duration_days(self):
        """Durée du voyage en jours"""
        return (self.end_date - self.start_date).days
    
    def is_over_budget(self):
        """Vérifier si le budget est dépassé"""
        return self.actual_spent > self.estimated_budget


# ============================================
# SIGNAL POUR CRÉER AUTOMATIQUEMENT UN WALLET
# ============================================

@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    """
    Crée automatiquement un wallet pour les utilisateurs Premium/Business
    """
    if created:
        try:
            if instance.subscription.is_premium:
                Wallet.objects.get_or_create(
                    user=instance,
                    defaults={'balance': 0.00, 'currency': 'EUR'}
                )
                print(f"✅ [WALLET] Portefeuille créé pour {instance.username}")
        except Exception as e:
            print(f"⚠️ [WALLET] Impossible de créer le wallet : {e}")
