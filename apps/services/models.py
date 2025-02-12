from django.db import models
from django.utils.translation import gettext_lazy as _

class Service(models.Model):
    name = models.CharField(_("Nom du service"), max_length=200)
    description = models.TextField(_("Description"))
    image = models.ImageField(_("Image"), upload_to="services/")
    price = models.DecimalField(_("Prix"), max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")

    def __str__(self):
        return self.name

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
