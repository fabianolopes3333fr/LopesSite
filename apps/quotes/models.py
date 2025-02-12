from django.db import models
from django.utils.translation import gettext_lazy as _

class Quote(models.Model):
    name = models.CharField(_("Nom"), max_length=100)
    email = models.EmailField(_("Email"))
    phone = models.CharField(_("Téléphone"), max_length=20)
    service = models.CharField(_("Service demandé"), max_length=200)
    area = models.DecimalField(_("Surface (m²)"), max_digits=10, decimal_places=2)
    details = models.TextField(_("Détails supplémentaires"))
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    status = models.CharField(_("Statut"), max_length=20, choices=[
        ('pending', _('En attente')),
        ('processed', _('Traité')),
        ('completed', _('Terminé')),
    ], default='pending')

    class Meta:
        verbose_name = _("Devis")
        verbose_name_plural = _("Devis")

    def __str__(self):
        return f"Devis de {self.name} pour {self.service}"
