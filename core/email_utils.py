import uuid
from datetime import datetime, timedelta
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site

def send_welcome_email(user, first_name, site_url, language='fr'):
    """
    Envoie un email de bienvenue à un nouvel utilisateur
    
    Args:
        user: L'utilisateur à qui envoyer l'email
        first_name: Le prénom de l'utilisateur
        site_url: L'URL de base du site
        language: La langue de l'email ('fr' ou 'en')
    """
    # Définition des textes en fonction de la langue
    if language == 'en':
        subject = "Welcome to Socialite!"
        template = 'emails/welcome_email_en.html'
    else:  # français par défaut
        subject = "Bienvenue sur Socialite !"
        template = 'emails/welcome_email.html'
    
    # Rendu du template HTML
    context = {
        'first_name': first_name,
        'site_url': site_url,
        'unsubscribe_url': f"{site_url}/unsubscribe"
    }
    
    html_content = render_to_string(template, context)
    
    # Création de l'email
    email = EmailMultiAlternatives(
        subject=subject,
        body=html_content,  # Version texte brut générée automatiquement
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_content, "text/html")
    
    try:
        email.send(fail_silently=False)
        return True
    except Exception as e:
        error_msg = f"Error sending welcome email: {e}" if language == 'en' else f"Erreur lors de l'envoi de l'email de bienvenue: {e}"
        print(error_msg)
        return False

def generate_verification_token():
    """Génère un jeton de vérification unique"""
    return str(uuid.uuid4())

def send_verification_email(request, user, user_profile, language='fr'):
    """
    Envoie un email de vérification à l'utilisateur
    
    Args:
        request: Objet HttpRequest
        user: L'utilisateur à qui envoyer l'email
        user_profile: Le profil utilisateur
        language: La langue de l'email ('fr' ou 'en')
    """
    try:
        # Générer un nouveau jeton de vérification
        token = generate_verification_token()
        
        # Mettre à jour le profil utilisateur avec le nouveau jeton
        user_profile.email_verification_token = token
        user_profile.email_verification_sent_at = timezone.now()
        user_profile.save()
        
        # Construire l'URL de vérification
        current_site = get_current_site(request)
        verification_url = request.build_absolute_uri(
            reverse('verify_email', kwargs={'token': token})
        )
        
        # Déterminer le template et le sujet en fonction de la langue
        if language == 'en':
            subject = f"Verify your email - {current_site.name}"
            template = 'emails/verify_email_en.html'
        else:  # français par défaut
            subject = f"Vérifiez votre adresse email - {current_site.name}"
            template = 'emails/verify_email.html'
        
        # Préparer le contexte pour le template
        context = {
            'user': user,
            'verification_url': verification_url,
            'site_name': current_site.name,
            'site_url': f"https://{current_site.domain}",
            'expiration_hours': 24,  # Lien valable 24h
        }
        
        # Rendu du template HTML
        html_content = render_to_string(template, context)
        
        # Création de l'email
        email = EmailMultiAlternatives(
            subject=subject,
            body=html_content,  # Version texte brut générée automatiquement
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
            headers={
                'X-Auto-Response-Suppress': 'OOF, AutoReply',
                'Precedence': 'bulk',
            },
        )
        email.attach_alternative(html_content, "text/html")
        
        # Envoyer l'email
        email.send(fail_silently=False)
        return True
        
    except Exception as e:
        logger.error(f"Error in send_verification_email: {e}", exc_info=True)
        return False


def send_password_reset_code_email(request, user, user_profile, code, language='fr'):
    """Envoie un email contenant le code de réinitialisation du mot de passe."""
    try:
        current_site = get_current_site(request)
        site_name = current_site.name
        site_url = request.build_absolute_uri('/')[:-1]

        if language == 'en':
            subject = f"{site_name} - Password reset code"
            template = 'emails/password_reset_code_en.html'
        else:
            subject = f"{site_name} - Code de réinitialisation du mot de passe"
            template = 'emails/password_reset_code_fr.html'

        context = {
            'user': user,
            'code': code,
            'site_name': site_name,
            'site_url': site_url,
            'support_email': settings.DEFAULT_FROM_EMAIL,
            'valid_minutes': 15,
        }

        html_content = render_to_string(template, context)

        email = EmailMultiAlternatives(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email de réinitialisation: {e}")
        return False


def send_login_otp_email(request, user, code, language='fr'):
    """Envoie un email contenant le code OTP de connexion (2FA)."""
    try:
        current_site = get_current_site(request)
        site_name = current_site.name
        site_url = request.build_absolute_uri('/')[:-1]

        if language == 'en':
            subject = f"{site_name} - Your sign-in code"
            template = 'emails/login_otp_en.html'
        else:
            subject = f"{site_name} - Votre code de connexion"
            template = 'emails/login_otp_fr.html'

        context = {
            'user': user,
            'code': code,
            'site_name': site_name,
            'site_url': site_url,
            'support_email': settings.DEFAULT_FROM_EMAIL,
            'valid_minutes': 10,
        }

        html_content = render_to_string(template, context)

        email = EmailMultiAlternatives(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email OTP: {e}")
        return False
