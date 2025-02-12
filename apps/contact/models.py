from django.db import models
from django.utils.translation import gettext_lazy as _

class Contact(models.Model):
    name = models.CharField(_("Nom"), max_length=100)
    email = models.EmailField(_("Email"))
    phone = models.CharField(_("Téléphone"), max_length=20)
    message = models.TextField(_("Message"))
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)

    class Meta:
        verbose_name = _("Contact")
        verbose_name_plural = _("Contacts")

    def __str__(self):
        return f"Message de {self.name}"
