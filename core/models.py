from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

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
# SIGNAL IMPORTANT : Créer le profil automatiquement
# ============================================
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal pour créer automatiquement un profil quand un utilisateur est créé
    """
    if created:
        UserProfile.objects.create(user=instance)


# ============================================
# MODÈLES POUR LE SYSTÈME DE POSTS
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
    # Ces compteurs sont mis à jour automatiquement pour éviter des requêtes SQL lourdes
    likes_count = models.IntegerField(default=0, help_text="Nombre de likes")
    comments_count = models.IntegerField(default=0, help_text="Nombre de commentaires")
    shares_count = models.IntegerField(default=0, help_text="Nombre de partages")
    
    # Visibilité du post
    VISIBILITY_CHOICES = [
        ('public', 'Public'),          # Tout le monde peut voir
        ('friends', 'Amis seulement'), # Seulement les amis
        ('private', 'Privé'),          # Seulement moi
    ]
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)  # Date de création (automatique)
    updated_at = models.DateTimeField(auto_now=True)      # Date de modification (automatique)
    
    # Post partagé (si c'est un partage d'un autre post)
    shared_post = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='shares')
    
    class Meta:
        ordering = ['-created_at']  # Les posts les plus récents en premier
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
    # Si parent=None, c'est un commentaire principal
    # Sinon, c'est une réponse à un autre commentaire
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Image optionnelle dans le commentaire
    image = models.ImageField(upload_to='comments/images/', blank=True, null=True)
    
    # Statistiques
    likes_count = models.IntegerField(default=0)
    
    # Date
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']  # Les commentaires les plus anciens en premier
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
    
    # Réaction sur un post OU un commentaire (pas les deux en même temps)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='reactions')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='reactions')
    
    # Type de réaction
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES, default='like')
    
    # Date
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Contrainte : un utilisateur ne peut réagir qu'une fois par post/commentaire
        # Mais il peut changer sa réaction
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
    Permet de tracker qui a partagé quel post et quand.
    """
    # Utilisateur qui partage le post
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_posts')
    
    # Post original qui est partagé
    original_post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_shares')
    
    # Message optionnel lors du partage (comme sur Facebook/Twitter)
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
            # If mongo unavailable, be conservative: block review
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
