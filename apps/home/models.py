from django.db import models
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

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
    PLATFORM_CHOICES = [
        ('google', 'Google'),
        ('site', 'Site Web'),
        ('facebook', 'Facebook'),
    ]

    author_name = models.CharField(_('nom de l\'auteur'), max_length=100, blank=True, help_text=_('Nom de l\'auteur'))
    author_title = models.CharField(_('titre/profession'), max_length=100, blank=True, help_text=_('Titre/profession de l\'auteur'))
    author_image = models.ImageField(_('photo'), upload_to='testimonials/', null=True, blank=True, help_text=_('Photo de l\'auteur'))
    company = models.CharField(_('entreprise'), max_length=100, blank=True, help_text=_('Entreprise de l\'auteur'))
    rating = models.IntegerField(
        _('note'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5,
        help_text=_('Note de l\'auteur (entre 1 et 5)')
    )
    text = models.TextField(_('témoignage'), blank=True, help_text=_('Témoignage de l\'auteur'))
    platform = models.CharField(
        _('plateforme'),
        max_length=20,
        choices=PLATFORM_CHOICES,
        default='google',
        help_text=_('Plateforme de l\'auteur')
    )
    external_id = models.CharField(
        _('ID externe'),
        max_length=100,
        blank=True,
        help_text=_('ID de référence de la plateforme externe')
    )
    verified = models.BooleanField(_('vérifié'), default=False, help_text=_('Si le témoignage est vérifié' 'dans la page d\'accueil'))
    featured = models.BooleanField(_('mis en avant'), default=False, help_text=_('Si le témoignage est mis en avant' 'dans la page d\'accueil'))
    date_posted = models.DateTimeField(_('date de publication'), default=timezone.now, help_text=_('Date de publication du témoignage' 'dans la page d\'accueil'))
    date_imported = models.DateTimeField(_('date d\'importation'), default=timezone.now, help_text=_('Date d\'importation du témoignage' 'dans la base de données'))
    active = models.BooleanField(_('actif'), default=True, help_text=_('Si le témoignage est actif' 'dans la page d\'accueil'))

    class Meta:
        verbose_name = _('témoignage')
        verbose_name_plural = _('témoignages')
        ordering = ['-date_posted', '-rating']

    def __str__(self):
        return f"{self.author_name} - {self.get_platform_display()}"

    def get_platform_display(self) -> str:
        """Retorna o texto formatado da plataforma"""
        return dict(self.PLATFORM_CHOICES).get(self.platform, self.platform)

    def get_platform_icon(self) -> str:
        """Retorna o ícone correspondente à plataforma"""
        icons = {
            'google': 'fab fa-google',
            'site': 'fas fa-globe',
            'facebook': 'fab fa-facebook'
        }
        return icons.get(self.platform, 'fas fa-star')

class GoogleReviewsSettings(models.Model):
    api_key = models.CharField(
        _('clé API Google'),
        max_length=255,
        blank=False,
        help_text=_('Votre clé API Google Places')
    )
    place_id = models.CharField(
        _('ID de l\'établissement'),
        max_length=255,
        blank=False,
        help_text=_('L\'ID Google My Business de votre établissement')
    )
    last_sync = models.DateTimeField(
        _('dernière synchronisation'),
        null=True,
        blank=True
    )
    auto_import = models.BooleanField(
        _('importation automatique'),
        default=True,
        help_text=_('Importer automatiquement les nouveaux avis Google')
    )
    min_rating = models.IntegerField(
        _('note minimum'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=4,
        help_text=_('Note minimum pour l\'importation automatique')
    )

    class Meta:
        verbose_name = _('configuration Google Reviews')
        verbose_name_plural = _('configurations Google Reviews')

    def __str__(self):
        return f"Configuration Google Reviews ({self.place_id})"

    def save(self, *args, **kwargs):
        # Garantir que só existe uma configuração
        if not self.pk and GoogleReviewsSettings.objects.exists():
            raise ValidationError(_("Il ne peut y avoir qu'une seule configuration"))
        super().save(*args, **kwargs)
