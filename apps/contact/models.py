from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

class Contact(models.Model):
    STATUS_CHOICES = [
        ('new', _('Nouveau')),
        ('in_progress', _('En cours')),
        ('resolved', _('Résolu')),
    ]
    name = models.CharField(_("Nom"), max_length=100)
    email = models.EmailField(_("Email"))
    phone = models.CharField(_("Téléphone"), max_length=20, validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')]) 
    subject = models.CharField(_("Sujet"), max_length=200, blank=True)
    message = models.TextField(_("Message"))
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    status = models.CharField(_("Statut"), max_length=20, choices=STATUS_CHOICES, default='new')

    def __str__(self):
        return f"{self.name} - {self.subject}"
    class Meta:
        verbose_name = _("Message de contact")
        verbose_name_plural = _("Messages de contact")
        ordering = ['-created_at']

class CompanyInfo(models.Model):
    name = models.CharField(_("Nom de l'entreprise"), max_length=100)
    address = models.TextField(_("Adresse"))
    postal_code = models.CharField(
        max_length=5, verbose_name=_("Code postal"), help_text=_("Code postal"), default="00000",
        validators=[
            RegexValidator(
                regex=r'^\d{5}$',
                message='Le code postal doit contenir exactement 5 chiffres.',
                code='invalid_postal_code'
            )
        ]
    )
    city = models.CharField(max_length=100, verbose_name=_("Ville"), help_text=_("Ville"), default="Vile")
    phone = models.CharField(_("Téléphone"), max_length=20, help_text=_("Téléphone"))
    email = models.EmailField(_("Email"), help_text=_("Email"))
    opening_hours = models.TextField(_("Horaires d'ouverture"), help_text=_("Horaires d'ouverture"))
    latitude = models.FloatField(_("Latitude"), help_text=_("Latitude"))
    longitude = models.FloatField(_("Longitude"), help_text=_("Longitude"))
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Informations de l'entreprise")
        verbose_name_plural = _("Informations de l'entreprise")
