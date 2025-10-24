from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from .models import UserProfile
from datetime import date
from PIL import Image
from django.contrib.auth.forms import PasswordChangeForm

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'email': 'Adresse email',
        }
        help_texts = {
            'first_name': 'Votre prénom (2-50 caractères)',
            'last_name': 'Votre nom de famille (2-50 caractères)',
            'email': 'Votre adresse email principale',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Entrez votre prénom',
                'required': True,
                'minlength': '2',
                'maxlength': '50',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Entrez votre nom',
                'required': True,
                'minlength': '2',
                'maxlength': '50',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'votre.email@exemple.com',
                'required': True,
            }),
        }
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name and len(first_name) < 2:
            raise ValidationError('Le prénom doit contenir au moins 2 caractères.')
        if first_name and not first_name.replace(' ', '').replace('-', '').isalpha():
            raise ValidationError('Le prénom ne doit contenir que des lettres.')
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name and len(last_name) < 2:
            raise ValidationError('Le nom doit contenir au moins 2 caractères.')
        if last_name and not last_name.replace(' ', '').replace('-', '').isalpha():
            raise ValidationError('Le nom ne doit contenir que des lettres.')
        return last_name
        
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'location', 'birth_date', 
            'avatar', 'cover_image',
            'website', 'facebook', 'instagram', 'twitter',
            'favorite_destinations', 'travel_style'
        ]
        labels = {
            'bio': 'Biographie',
            'location': 'Lieu de résidence',
            'birth_date': 'Date de naissance',
            'avatar': 'Photo de profil',
            'cover_image': 'Photo de couverture',
            'website': 'Site web',
            'facebook': 'Facebook',
            'instagram': 'Instagram',
            'twitter': 'Twitter',
            'favorite_destinations': 'Destinations favorites',
            'travel_style': 'Style de voyage',
        }
        help_texts = {
            'bio': 'Présentez-vous en quelques mots (500 caractères maximum)',
            'location': 'Ville ou pays où vous résidez',
            'birth_date': 'Votre date de naissance (pour afficher votre âge)',
            'avatar': 'Format accepté : JPG, PNG, WEBP (max 5MB, minimum 100x100px)',
            'cover_image': 'Format accepté : JPG, PNG, WEBP (max 10MB)',
            'website': 'URL complète de votre site web (ex: https://monsite.com)',
            'facebook': 'Votre nom d\'utilisateur Facebook (sans le lien complet)',
            'instagram': 'Votre nom d\'utilisateur Instagram (sans @)',
            'twitter': 'Votre nom d\'utilisateur Twitter (sans @)',
            'favorite_destinations': 'Listez vos destinations de voyage préférées',
            'travel_style': 'Quel type de voyageur êtes-vous ?',
        }
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 5,
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Parlez de vous, vos passions, vos intérêts...',
                'maxlength': '500',
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Paris, France',
            }),
            'birth_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'max': date.today().isoformat(),
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'https://monsite.com',
            }),
            'facebook': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'votre.nom',
            }),
            'instagram': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'votre_nom',
            }),
            'twitter': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'votre_nom',
            }),
            'favorite_destinations': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Exemple : Paris, Tokyo, New York...',
            }),
            'travel_style': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            }),
        }
    
    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            if birth_date > date.today():
                raise ValidationError('La date de naissance ne peut pas être dans le futur.')
            
            # Vérifier que l'utilisateur a au moins 13 ans
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 13:
                raise ValidationError('Vous devez avoir au moins 13 ans pour utiliser cette plateforme.')
        
        return birth_date
    
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Vérifier la taille du fichier (max 5MB)
            if avatar.size > 5 * 1024 * 1024:
                raise ValidationError('La taille de l\'image ne doit pas dépasser 5 MB.')
            
            # Vérifier le format
            valid_extensions = ['jpg', 'jpeg', 'png', 'webp']
            ext = avatar.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise ValidationError(f'Format non accepté. Utilisez : {", ".join(valid_extensions).upper()}')
            
            # Vérifier les dimensions minimales
            try:
                img = Image.open(avatar)
                if img.width < 100 or img.height < 100:
                    raise ValidationError('L\'image doit faire au moins 100x100 pixels.')
            except Exception:
                raise ValidationError('Fichier image invalide.')
        
        return avatar
    
    def clean_cover_image(self):
        cover_image = self.cleaned_data.get('cover_image')
        if cover_image:
            # Vérifier la taille du fichier (max 10MB)
            if cover_image.size > 10 * 1024 * 1024:
                raise ValidationError('La taille de l\'image ne doit pas dépasser 10 MB.')
            
            # Vérifier le format
            valid_extensions = ['jpg', 'jpeg', 'png', 'webp']
            ext = cover_image.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise ValidationError(f'Format non accepté. Utilisez : {", ".join(valid_extensions).upper()}')
        
        return cover_image
    
    def clean_website(self):
        website = self.cleaned_data.get('website')
        if website:
            validator = URLValidator()
            try:
                validator(website)
            except ValidationError:
                raise ValidationError('Veuillez entrer une URL valide (ex: https://monsite.com)')
        return website

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='Mot de passe actuel',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-500 focus:border-red-500',
            'placeholder': '••••••••',
        }),
        help_text='Entrez votre mot de passe actuel pour confirmer les changements'
    )
    new_password1 = forms.CharField(
        label='Nouveau mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-green-500 focus:border-green-500',
            'placeholder': '••••••••',
        }),
        help_text='Minimum 8 caractères, avec lettres et chiffres'
    )
    new_password2 = forms.CharField(
        label='Confirmer le nouveau mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-green-500 focus:border-green-500',
            'placeholder': '••••••••',
        }),
        help_text='Saisissez à nouveau votre nouveau mot de passe'
    )