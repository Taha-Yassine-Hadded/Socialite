from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    # Lien avec l'utilisateur Django
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
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
    
    def __str__(self):
        return f"Profil de {self.user.username}"

# Signal pour créer automatiquement un profil quand un utilisateur est créé
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
 