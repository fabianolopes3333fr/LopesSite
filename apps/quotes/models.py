from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.users.models import CustomUser
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from typing import List, Tuple
from django.utils import timezone


class Supplier(models.Model):
    name = models.CharField(_('Nom du fournisseur'), max_length=200)
    code = models.CharField(_('Code'), max_length=50, unique=True)
    contact_name = models.CharField(_('Contact'), max_length=100)
    email = models.EmailField(_('Email'))
    phone = models.CharField(_('Téléphone'), max_length=20)
    address = models.TextField(_('Adresse'))
    active = models.BooleanField(_('Actif'), default=True)
    minimum_order = models.DecimalField(
        _('Commande minimum'), 
        max_digits=10, 
        decimal_places=2,
        default=0
    )
    lead_time = models.IntegerField(_('Délai de livraison (jours)'), default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Fournisseur')
        verbose_name_plural = _('Fournisseurs')
        
        
class PaintCategory(models.Model):
    name = models.CharField(_('Nom'), max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(_('Description'), blank=True)
    image = models.ImageField(upload_to='categories/', blank=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='children'
    )
    order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = _('Catégorie')
        verbose_name_plural = _('Catégories')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

### Produto (Pintura)
class Paint(models.Model):
    FINISH_CHOICES = [
        ('matte', _('Mat')),
        ('satin', _('Satin')),
        ('gloss', _('Brillant')),
        ('semi_gloss', _('Semi-brillant')),
    ]
    
    name = models.CharField(_('Nom'), max_length=200)
    slug = models.SlugField(unique=True)
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.CASCADE,
        related_name='paints'
    )
    category = models.ForeignKey(
        PaintCategory,
        on_delete=models.SET_NULL,
        null=True
    )
    sku = models.CharField(_('SKU'), max_length=50, unique=True)
    description = models.TextField(_('Description'))
    features = models.JSONField(_('Caractéristiques'), default=dict)
    technical_sheet = models.FileField(
        upload_to='technical_sheets/',
        blank=True
    )
    finish = models.CharField(
        _('Finition'),
        max_length=20,
        choices=FINISH_CHOICES
    )
    coverage = models.DecimalField(
        _('Couverture (m²/L)'),
        max_digits=5,
        decimal_places=2
    )
    drying_time = models.CharField(_('Temps de séchage'), max_length=100)
    base_price = models.DecimalField(
        _('Prix de base'),
        max_digits=10,
        decimal_places=2
    )
    stock_quantity = models.IntegerField(_('Quantité en stock'))
    min_stock = models.IntegerField(_('Stock minimum'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

### Variante do Produto
class PaintVariant(models.Model):
    paint = models.ForeignKey(
        Paint,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    color_code = models.CharField(_('Code couleur'), max_length=20)
    color_name = models.CharField(_('Nom couleur'), max_length=100)
    size = models.DecimalField(_('Taille (L)'), max_digits=5, decimal_places=2)
    price_adjustment = models.DecimalField(
        _('Ajustement de prix'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    stock_quantity = models.IntegerField(_('Quantité en stock'))
    image = models.ImageField(upload_to='paint_variants/')


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('paid', _('Payé')),
        ('preparing', _('En préparation')),
        ('shipped', _('Expédié')),
        ('delivered', _('Livré')),
        ('cancelled', _('Annulé')),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='customer_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name='shipping_orders')
    tracking_number = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    paint_variant = models.ForeignKey(PaintVariant, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)


class Quote(models.Model):
    
    STATUS_CHOICES: List[Tuple[str, str]] = [
        ('pending', _('En attente')),
        ('in_review', _('En cours de révision')),
        ('approved', _('Approuvé')),
        ('rejected', _('Rejeté')),
        ('canceled', _('Annulé'))
    ]

    TYPE_CHOICES: List[Tuple[str, str]] = [
        ('interior', _('Peinture Intérieure')),
        ('exterior', _('Peinture Extérieure')),
        ('commercial', _('Peinture Commerciale')),
        ('industrial', _('Peinture Industrielle')),
        ('decorative', _('Peinture Décorative')),
        ('floor', _('Parquet Flottant')),
        ('wallpaper', _('Papier Peint')),
        ('glass', _('Toile de Verre'))
    ]
    
    CONTACT_PREFERENCES: List[Tuple[str, str]] = [
        ('email', 'Email'),
        ('phone', _('Téléphone')),
        ('both', _('Les deux'))
    ]
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='quotes',
        null=True,
        blank=True
    )
    # Informações do Projeto
    project_type = models.CharField(
        _('type de projet'),
        max_length=50,
        choices=TYPE_CHOICES,
        default='interior'
    )
    
    area_size  = models.DecimalField(
        _("Surface (m²)"), 
        max_digits=10, 
        decimal_places=2
    )
    
    description = models.TextField(_('Description du projet'), null=True, blank=True)
    desired_start_date = models.DateField(
        _('date de début souhaitée'),
        default=timezone.now
        
    )
    
    # Informações de Localização
    address = models.CharField(_('Adresse'),max_length=255, null=True, blank=True)
    postal_code = models.CharField(_('Code Postal'), max_length=10, null=True, blank=True)
    city = models.CharField(_('Ville'), max_length=100, null=True, blank=True)
    
    # Informações BásicasInformações de Contato Adicionais
    phone_number = models.CharField(_("Téléphone"), max_length=20)
    contact_preference = models.CharField(
        _('préférence de contact'),
        max_length=20,
        choices=CONTACT_PREFERENCES,
        default='email'
    )
    # Campos de Sistema
    status = models.CharField(
        _("Statut"), 
        max_length=20, 
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    class Meta:
        verbose_name = _('devis')
        verbose_name_plural = _('devis')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Devis #{self.id} - {self.get_project_type_display()}"

    def get_display_value(self, choices: List[Tuple[str, str]], value: str) -> str:
        """Método auxiliar para obter o valor de exibição de choices"""
        return dict(choices).get(value, value)

    def get_project_type_display(self) -> str:
        """Retorna o valor formatado do tipo de projeto"""
        return self.get_display_value(self.TYPE_CHOICES, self.project_type)

    def get_status_display(self) -> str:
        """Retorna o valor formatado do status"""
        return self.get_display_value(self.STATUS_CHOICES, self.status)

    def get_contact_preference_display(self) -> str:
        """Retorna o valor formatado da preferência de contato"""
        return self.get_display_value(self.CONTACT_PREFERENCES, self.contact_preference)
        

    

class QuotePhoto(models.Model):
    image = models.ImageField(upload_to='quotes/photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    caption = models.CharField(max_length=200, blank=True)

class QuoteStatusUpdate(models.Model):
    quote = models.ForeignKey(
        Quote,
        on_delete=models.CASCADE,
        related_name='status_updates'
    )
    status = models.CharField(max_length=20, choices=Quote.STATUS_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True
    )