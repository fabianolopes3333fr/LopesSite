from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.users.models import CustomUser
from django.utils.text import slugify


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
    name = models.CharField(_("Nom"), max_length=100)
    email = models.EmailField(_("Email"))
    phone = models.CharField(_("Téléphone"), max_length=20)
    service = models.CharField(_("Service demandé"), max_length=200)
    area = models.DecimalField(_("Surface (m²)"), max_digits=10, decimal_places=2)
    details = models.TextField(_("Détails supplémentaires"))
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    status = models.CharField(_("Statut"), max_length=20, choices=[
        ('pending', _('En attente')),
        ('processed', _('Traité')),
        ('completed', _('Terminé')),
    ], default='pending')

    class Meta:
        verbose_name = _("Devis")
        verbose_name_plural = _("Devis")

    def __str__(self):
        return f"Devis de {self.name} pour {self.service}"
