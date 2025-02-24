# apps/config/models.py
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
import json
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse
from django_ckeditor_5.fields import CKEditor5Field
from colorfield.fields import ColorField
from django.contrib.auth.models import User
from mptt.models import MPTTModel, TreeForeignKey
from django.utils import timezone
from datetime import datetime




class FieldGroup(models.Model):
    name = models.CharField(_('Nom du groupe'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    order = models.PositiveIntegerField(_('Ordre'), default=0)

    class Meta:
        verbose_name = _('Groupe de champs')
        verbose_name_plural = _('Groupes de champs')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Redirect(models.Model):
    old_path = models.CharField(_('Ancien chemin'), max_length=200, unique=True)
    new_path = models.CharField(_('Nouveau chemin'), max_length=200)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)

    class Meta:
        verbose_name = _('Redirection')
        verbose_name_plural = _('Redirections')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.old_path} -> {self.new_path}"
    
class CustomField(models.Model):
    FIELD_TYPES = (
        ('text', _('Texte')),
        ('textarea', _('Zone de texte')),
        ('number', _('Nombre')),
        ('date', _('Date')),
        ('boolean', _('Booléen')),
        ('choice', _('Choix')),
        ('file', _('Fichier')),
        ('image', _('Image')),
    )

    name = models.CharField(_('Nom'), max_length=100)
    field_type = models.CharField(_('Type de champ'), max_length=20, choices=FIELD_TYPES)
    required = models.BooleanField(_('Obligatoire'), default=False)
    choices = models.TextField(_('Choix'), blank=True, help_text=_('Pour le type "choix", entrez les options séparées par des virgules'))
    group = models.ForeignKey(FieldGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='fields', verbose_name=_('Groupe'))
    order = models.PositiveIntegerField(_('Ordre'), default=0)
    
    class Meta:
        verbose_name = _('Champ personnalisé')
        verbose_name_plural = _('Champs personnalisés')
        ordering = ['group', 'order', 'name']

    def __str__(self):
        return self.name

class CustomFieldValue(models.Model):
    field = models.ForeignKey(CustomField, on_delete=models.CASCADE)
    page = models.ForeignKey('Page', on_delete=models.CASCADE, related_name='custom_field_values')
    value = models.TextField(_('Valeur'))

    class Meta:
        unique_together = ('field', 'page')
        verbose_name = _('Valeur de champ personnalisé')
        verbose_name_plural = _('Valeurs de champs personnalisés')

    def __str__(self):
        return f"{self.field.name}: {self.value}" 

    def clean(self):
        super().clean()
        field_type = self.field.field_type

        if field_type == 'text':
            if len(self.value) > 255:
                raise ValidationError(_('Le texte ne peut pas dépasser 255 caractères.'))

        elif field_type == 'textarea':
            if len(self.value) > 1000:
                raise ValidationError(_('Le texte ne peut pas dépasser 1000 caractères.'))

        elif field_type == 'number':
            try:
                num_value = float(self.value)
                MinValueValidator(-1000000)(num_value)
                MaxValueValidator(1000000)(num_value)
            except ValueError:
                raise ValidationError(_('Veuillez entrer un nombre valide.'))

        elif field_type == 'date':
            try:
                datetime.strptime(self.value, '%Y-%m-%d')
            except ValueError:
                raise ValidationError(_('Veuillez entrer une date valide au format YYYY-MM-DD.'))

        elif field_type == 'boolean':
            if self.value.lower() not in ['true', 'false', '1', '0']:
                raise ValidationError(_('Veuillez entrer une valeur booléenne valide (true/false ou 1/0).'))

        elif field_type == 'choice':
            choices = [choice.strip() for choice in self.field.choices.split(',')]
            if self.value not in choices:
                raise ValidationError(_('Veuillez sélectionner une option valide.'))

        elif field_type in ['file', 'image']:
            # Aqui você pode adicionar validação para arquivos/imagens se necessário
            pass

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    

class Page(MPTTModel):
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('review', _('Review')),
        ('scheduled', _('Scheduled')),
        ('published', _('Published')),
        ('archived', _('Archived')),
    ]
    
    

    title = models.CharField(_('Titre'), max_length=200)
    slug = models.SlugField(_('Slug'),max_length=200, unique=True)
    content = CKEditor5Field(_('Content'), config_name='default')
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_for = models.DateTimeField(_('Programmé pour'), null=True,blank=True, help_text=_('Date et heure de publication programmée'))
    custom_fields = models.ManyToManyField(CustomField, through=CustomFieldValue, blank=True)

    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    published_at = models.DateTimeField(_('Published at'), null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='pages_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='pages_updated')

    level = models.PositiveIntegerField(default=0, editable=False)
    lft = models.PositiveIntegerField(default=0, editable=False)
    rght = models.PositiveIntegerField(default=0, editable=False)
    tree_id = models.PositiveIntegerField(default=0, editable=False)
    
    # SEO fields
    meta_title = models.CharField(_('Meta Title SEO'), max_length=70, blank=True)
    meta_description = models.TextField(_('Meta Description SEO'), max_length=160, blank=True)
    meta_keywords = models.CharField(_('Meta Keywords SEO'), max_length=255, blank=True)
    
    # Open Graph fields
    og_title = models.CharField(_('OG Title'), max_length=60, blank=True)
    og_description = models.CharField(_('OG Description'), max_length=160, blank=True)
    og_image = models.ImageField(_('OG Image'), upload_to='og_images/', blank=True)
    og_type = models.CharField(_("OG Type"), max_length=50, default='website')
    
    # Schema.org fields
    schema_type = models.CharField(_('Schema Type'), max_length=50, default='WebPage')
    schema_name = models.CharField(_('Schema Name'), max_length=200, blank=True)
    schema_description = models.TextField(_('Schema Description'), blank=True)
    
    # Campos adicionais
    canonical_url = models.URLField(_("URL Canonique"), blank=True)
    robots = models.CharField(_("Robots"), max_length=50, default='index,follow')
    
    css_class = models.CharField(
        _('classe CSS'),
        max_length=100,
        blank=True,
        help_text=_('Classes CSS supplémentaires pour cette page')
    )
    js_code = models.TextField(
        _('code JavaScript'),
        blank=True,
        help_text=_('Code JavaScript spécifique à cette page')
    )

    class Meta:
        verbose_name = _('page')
        verbose_name_plural = _('pages')
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
    def get_custom_field_value(self, field_name):
        try:
            custom_field = self.custom_fields.get(name=field_name)
            return CustomFieldValue.objects.get(field=custom_field, page=self).value
        except (CustomField.DoesNotExist, CustomFieldValue.DoesNotExist):
            return None

    def set_custom_field_value(self, field_name, value):
        custom_field, created = CustomField.objects.get_or_create(name=field_name)
        CustomFieldValue.objects.update_or_create(
            field=custom_field,
            page=self,
            defaults={'value': value}
        )
    def get_custom_fields_by_group(self):
        grouped_fields = {}
        for field_value in self.custom_field_values.select_related('field__group'):
            group = field_value.field.group
            if group not in grouped_fields:
                grouped_fields[group] = []
            grouped_fields[group].append(field_value)
        return grouped_fields

    def create_version(self, user):
        return PageVersionConfig.objects.create(
            page=self,
            content=self.content,
            created_by=user
        )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Verifica se o slug foi alterado
        if self.pk:
            old_page = Page.objects.get(pk=self.pk)
            if old_page.slug != self.slug:
                # Cria um redirecionamento
                
                Redirect.objects.create(
                    old_path=f'/{old_page.slug}/',
                    new_path=f'/{self.slug}/'
                )
        
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        elif self.status == 'scheduled' and not self.scheduled_for:
            raise ValueError(_("Une date de publication doit être définie pour les pages programmées."))
        
        super().save(*args, **kwargs)
        

    def get_absolute_url(self):
        return reverse('page_detail', kwargs={'slug': self.slug})

    
class PageVersionConfig(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='version_configs')
    content = CKEditor5Field(_('Content'))
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-created_at']

    
class SiteStyle(models.Model):
    # Colors
    primary_color = ColorField(_('couleur primaire'), default='#424e55')
    secondary_color = ColorField(_('couleur secondaire'), default='#5a666e')
    accent_color = ColorField(_('couleur d\'accent'), default='#68a138')
    
    # Typography
    font_family = models.CharField(
        _('police principale'),
        max_length=100,
        default='Arial, sans-serif'
    )
    heading_font = models.CharField(
        _('police des titres'),
        max_length=100,
        default='Arial, sans-serif'
    )
    
    # Sizes
    base_font_size = models.CharField(
        _('taille de police de base'),
        max_length=10,
        default='16px'
    )
    
    # Custom CSS
    custom_css = models.TextField(_('CSS personnalisé'), blank=True)
    # Cores adicionais
    text_color = ColorField(_('couleur du texte'), default='#333333')
    link_color = ColorField(_('couleur des liens'), default='#68a138')
    heading_color = ColorField(_('couleur des titres'), default='#424e55')
    
    # Tipografia adicional
    body_line_height = models.CharField(
        _('hauteur de ligne du corps'),
        max_length=10,
        default='1.6'
    )
    heading_line_height = models.CharField(
        _('hauteur de ligne des titres'),
        max_length=10,
        default='1.2'
    )
    
    # Layout
    container_width = models.CharField(
        _('largeur du conteneur'),
        max_length=10,
        default='1200px'
    )
    grid_gutter = models.CharField(
        _('gouttière de grille'),
        max_length=10,
        default='30px'
    )
    
    # Responsivo
    mobile_breakpoint = models.CharField(
        _('point de rupture mobile'),
        max_length=10,
        default='768px'
    )
    tablet_breakpoint = models.CharField(
        _('point de rupture tablette'),
        max_length=10,
        default='992px'
    )
    
    class Meta:
        verbose_name = _('style du site')
        verbose_name_plural = _('styles du site')

    def __str__(self):
        return _("Configuration du style")

class Menu(MPTTModel):
    name = models.CharField(_('nom'), max_length=100)
    url = models.CharField(_('URL'), max_length=255, blank=True)
    page = models.ForeignKey(
        Page,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='menu_items'
    )
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    icon = models.CharField(
        _('icône'),
        max_length=50,
        blank=True,
        help_text=_('Classe d\'icône FontAwesome')
    )
    target = models.CharField(
        _('cible'),
        max_length=20,
        choices=[
            ('_self', _('Même fenêtre')),
            ('_blank', _('Nouvelle fenêtre'))
        ],
        default='_self'
    )
    css_class = models.CharField(
        _('classe CSS'),
        max_length=100,
        blank=True
    )
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Description pour les menus déroulants')
    )
    order = models.IntegerField(_('ordre'), default=0)
    active = models.BooleanField(_('actif'), default=True)

    class Meta:
        verbose_name = _('menu')
        verbose_name_plural = _('menus')
        ordering = ['order']

    class MPTTMeta:
        order_insertion_by = ['order']

    def __str__(self):
        return self.name

