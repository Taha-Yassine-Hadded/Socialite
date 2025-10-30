# reports/urls.py
# Work of Dorsaf - URLs pour le système de signalement
from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'reports'

urlpatterns = [
    # URL pour soumettre un signalement
    path('report/', views.report_content, name='report_content'),
    
    # Tableau de bord administrateur
    path('admin/', views.report_dashboard, name='dashboard'),
    
    # Actions sur les signalements
    path('admin/update/<int:report_id>/', views.update_report_status, name='update_status'),
    path('admin/delete/<int:report_id>/', views.delete_reported_content, name='delete_content'),
]