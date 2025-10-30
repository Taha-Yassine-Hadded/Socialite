# Work of Dorsaf - Modèle de signalement
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Report(models.Model):
    class ReportType(models.TextChoices):
        INAPPROPRIATE = 'inappropriate', _('🔞 Inapproprié')
        SPAM = 'spam', _('💬 Spam ou publicité')
        HARASSMENT = 'harassment', _('😡 Harcèlement')
        FAKE = 'fake', _('⚠️ Fausse information')
        OTHER = 'other', _('🚫 Autre')

    class Status(models.TextChoices):
        PENDING = 'pending', _('En attente')
        RESOLVED = 'resolved', _('Résolu')
        IGNORED = 'ignored', _('Ignoré')

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    report_type = models.CharField(max_length=20, choices=ReportType.choices, verbose_name=_("Type de signalement"))
    message = models.TextField(blank=True, null=True, verbose_name=_("Message supplémentaire"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name=_("Statut"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Signalement')
        verbose_name_plural = _('Signalements')

    def __str__(self):
        return f"Signalement #{self.id} - {self.get_report_type_display()}"

    def get_status_color(self):
        """Retourne la classe CSS pour la couleur du statut"""
        colors = {
            'pending': 'warning',
            'resolved': 'success',
            'ignored': 'secondary'
        }
        return colors.get(self.status, 'secondary')