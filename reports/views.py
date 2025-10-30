# Work of Dorsaf - Vues pour la gestion des signalements
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from django.utils.translation import gettext as _
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q

from .models import Report

@login_required
@require_http_methods(["POST"])
def report_content(request):
    content_type_id = request.POST.get('content_type')
    object_id = request.POST.get('object_id')
    report_type = request.POST.get('report_type')
    message = request.POST.get('message', '')

    content_type = get_object_or_404(ContentType, id=content_type_id)
    content_object = get_object_or_404(content_type.model_class(), id=object_id)

    Report.objects.create(
        reporter=request.user,
        content_object=content_object,
        report_type=report_type,
        message=message
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': _('Merci pour votre signalement.')})
    
    messages.success(request, _('Merci pour votre signalement.'))
    return redirect(content_object.get_absolute_url())

@staff_member_required
def report_dashboard(request):
    reports = Report.objects.select_related('content_type', 'reporter')
    
    # Filtres
    status = request.GET.get('status', 'pending')
    if status in ['pending', 'resolved', 'ignored']:
        reports = reports.filter(status=status)
    
    # Stats
    stats = {
        'total': Report.objects.count(),
        'pending': Report.objects.filter(status='pending').count(),
        'resolved': Report.objects.filter(status='resolved').count(),
        'ignored': Report.objects.filter(status='ignored').count(),
    }
    
    return render(request, 'reports/dashboard.html', {
        'reports': reports.order_by('-created_at'),
        'title': _('Tableau de bord des signalements'),
        'current_status': status,
        'stats': stats,
    })

@staff_member_required
@require_POST
def update_report_status(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    action = request.POST.get('action')
    
    if action == 'approve':
        report.status = 'resolved'
        # Ici vous pouvez ajouter une logique pour supprimer le contenu signalé si nécessaire
        # report.content_object.delete()
        messages.success(request, _('Signalement marqué comme résolu.'))
    elif action == 'ignore':
        report.status = 'ignored'
        messages.info(request, _('Signalement ignoré.'))
    
    report.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'status': report.get_status_display(),
            'status_class': report.status
        })
    
    return redirect('reports:dashboard')

@staff_member_required
@require_http_methods(["POST"])
def delete_reported_content(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    
    if not hasattr(report.content_object, 'delete'):
        return JsonResponse(
            {'success': False, 'message': _('Impossible de supprimer ce contenu.')},
            status=400
        )
    
    # Marquer le signalement comme résolu
    report.status = 'resolved'
    report.save()
    
    # Supprimer le contenu signalé
    content_object = report.content_object
    content_object.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': _('Contenu supprimé avec succès.')
        })
    
    messages.success(request, _('Contenu supprimé avec succès.'))
    return redirect('reports:dashboard')