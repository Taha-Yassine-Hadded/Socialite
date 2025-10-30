# core/middleware.py
from django.shortcuts import redirect
from django.contrib import messages
from core.models import UsageQuota
from datetime import datetime
from dateutil.relativedelta import relativedelta

class QuotaResetMiddleware:
    """
    Middleware pour réinitialiser automatiquement les quotas mensuels
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                quota = request.user.quota
                
                # Vérifier si un mois s'est écoulé depuis le dernier reset
                one_month_ago = datetime.now() - relativedelta(months=1)
                if quota.last_reset.replace(tzinfo=None) < one_month_ago:
                    quota.reset_monthly_quotas()
                    
            except UsageQuota.DoesNotExist:
                # Créer le quota si il n'existe pas
                UsageQuota.objects.create(user=request.user)
        
        response = self.get_response(request)
        return response