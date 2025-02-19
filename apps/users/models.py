import re
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_('L e-mail doit être défini'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)
    
    
class CustomUser(AbstractUser, PermissionsMixin):
    
    letters_only = RegexValidator(
        regex=r'^[a-zA-ZÀ-ÿ\s\-]+$',
        message=_("Ce champ doit contenir uniquement des lettres, des espaces et des tirets.")
    )
    
    username = None
    email = models.EmailField(
        _('email address'), 
        unique=True, 
        max_length=255, 
        validators=[EmailValidator(message=_("Entrez une adresse email valide."))])
    
    frist_name = models.CharField(_('first name'), max_length=100, validators=[letters_only], blank=True)
    last_name = models.CharField(_('last name'), max_length=100, validators=[letters_only], blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_contractor = models.BooleanField(_('contractor status'), default=False)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    company_name = models.CharField(_('company name'), max_length=100, blank=True)
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name
    
    def clean(self):
        super().clean()
        # Validação adicional para o email
        if self.email:
            if CustomUser.objects.filter(email__iexact=self.email).exclude(pk=self.pk).exists():
                raise ValidationError({'email': _("Cette adresse email est déjà utilisée.")})
            
            
    def save(self, *args, **kwargs):
        if not self.username:
            get_email = self.email.split("@")[0]
            email = re.sub(r"[^a-zA-Z0-9]", "", get_email)
            self.username = email
        super(CustomUser, self).save(*args, **kwargs)



class ClientProfile(models.Model):
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    
    letters_only = RegexValidator(
        regex=r'^[a-zA-ZÀ-ÿ\s\-]+$',
        message=_("Ce champ doit contenir uniquement des lettres, des espaces et des tirets.")
    )
    
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(_('phone number'), max_length=15, blank=True, validators=[phone_regex])
    address = models.TextField(_('Adresse'))
    postal_code = models.CharField(_('Code Postal'), max_length=10)
    city = models.CharField(_('Ville'), max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        

    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"
    
    def clean(self):
        super().clean()
        
        if self.phone_number:
            numeric_phone = ''.join(filter(str.isdigit, self.telefone))
            if len(numeric_phone) < 10:
                raise ValidationError({'telefone': _("Le numéro de téléphone est trop court.")})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
    
class NewsletterSubscription(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
