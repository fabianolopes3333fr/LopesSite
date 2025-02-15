from django.db import models
from django.utils.translation import gettext_lazy as _

class Service(models.Model):
    CATEGORY_CHOICES = [
        ('residential', _('Résidentiel')),
        ('commercial', _('Commercial')),
        ('industrial', _('Industriel')),
        ('exterior', _('Extérieur')),
        ('interior', _('Intérieur')),
        ('other', _('Autre')),
    ]
    
    
    
    title = models.CharField(_("Title"), max_length=200, default="Service sans titre")
    name = models.CharField(_("Nom du service"), max_length=200)
    description = models.TextField(_("Description"))
    category = models.CharField(_("Catégorie"), max_length=20, choices=CATEGORY_CHOICES, default='other')
    icon_service = models.CharField(_("Icon"), max_length=50, default="fas fa-paint-roller")
    image = models.ImageField(_("Image"), upload_to="services/")
    price = models.DecimalField(_("Prix"), max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")

    def __str__(self):
        return self.title
    
class ServiceFeature(models.Model):
    service = models.ForeignKey(Service, related_name='features', on_delete=models.CASCADE)
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.service.title} - {self.description}"

class Project(models.Model):
    title = models.CharField(_("Titre"), max_length=200)
    description = models.TextField(_("Description"))
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="projects")
    image = models.ImageField(_("Image"), upload_to="projects/")
    completion_date = models.DateField(_("Date d'achèvement"))

    class Meta:
        verbose_name = _("Projet")
        verbose_name_plural = _("Projets")

    def __str__(self):
        return self.title
