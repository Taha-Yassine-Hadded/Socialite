from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    # NOUVEAU: Nom lisible pour l'interface d'administration
    verbose_name = 'Plateforme de Voyage'
    
    def ready(self):
        """
        Importer les signaux quand l'application est prête
        IMPORTANT : Cette étape charge core/signals.py
        """
        import core.signals
        print("✅ [APPS] Signaux d'abonnement chargés")