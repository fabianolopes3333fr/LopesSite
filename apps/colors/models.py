from django.db import models
from django.utils.translation import gettext_lazy as _

class Color(models.Model):
    COLOR_TYPES = [
        ('warm', _('Chaude')),
        ('cool', _('Froide')),
        ('neutral', _('Neutre')),
    ]
    
    name = models.CharField(_("Nom"), max_length=100)
    hex_code = models.CharField(_("Code Hexadécimal"), max_length=7)
    rgb_code = models.CharField(_("Code RGB"), max_length=20, null=True, blank=True)
    color_type = models.CharField(_('Type de Couleur'), max_length=10, choices=COLOR_TYPES, default='neutral')
    light_reflectance_value = models.FloatField(_('Valeur de Réflectance Lumineuse'), null=True, blank=True)

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

