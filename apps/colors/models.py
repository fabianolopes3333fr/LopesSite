from django.db import models
from django.utils.translation import gettext_lazy as _

class Color(models.Model):
    name = models.CharField(_("Nom"), max_length=100)
    hex_code = models.CharField(_("Code hexadécimal"), max_length=7)
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        verbose_name = _("Couleur")
        verbose_name_plural = _("Couleurs")

    def __str__(self):
        return self.name

class ColorCombination(models.Model):
    name = models.CharField(_("Nom"), max_length=100)
    colors = models.ManyToManyField(Color, related_name="combinations")
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        verbose_name = _("Combinaison de couleurs")
        verbose_name_plural = _("Combinaisons de couleurs")

    def __str__(self):
        return self.name
