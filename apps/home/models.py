from django.db import models
from django.utils.translation import gettext_lazy as _

class AboutUs(models.Model):
    title = models.CharField(_("Titre"), max_length=200)
    content = models.TextField(_("Contenu"))
    image = models.ImageField(_("Image"), upload_to="about_us/")

    class Meta:
        verbose_name = _("À propos de nous")
        verbose_name_plural = _("À propos de nous")

    def __str__(self):
        return self.title

class Testimonial(models.Model):
    name = models.CharField(_("Nom"), max_length=100)
    position = models.CharField(_("Poste"), max_length=100, blank=True)
    content = models.TextField(_("Témoignage"))
    image = models.ImageField(_("Photo"), upload_to="testimonials/", blank=True)

    class Meta:
        verbose_name = _("Témoignage")
        verbose_name_plural = _("Témoignages")

    def __str__(self):
        return self.name
