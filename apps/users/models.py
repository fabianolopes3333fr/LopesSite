import re
from django.utils import timezone
import pyotp
from django.conf import settings
from typing import Any, Optional, TypeVar
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator


T = TypeVar('T', bound='CustomUser')

class CustomUserManager(UserManager[T]):
    def create_user(self, email: str, password: Optional[str] = None, **extra_fields: Any) -> T:
        if not email:
            raise ValueError(_('L\'e-mail doit être défini'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields: Any) -> T:
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    letters_only = RegexValidator(
        regex=r'^[a-zA-ZÀ-ÿ\s\-]+$',
        message=_("Ce champ doit contenir uniquement des lettres, des espaces et des tirets.")
    )
    
    username = None
    email = models.EmailField(
        _('email address'), 
        unique=True, 
        max_length=255, 
        validators=[EmailValidator(message=_("Entrez une adresse email valide."))]
    )
    
    first_name = models.CharField(_('first name'), max_length=100, validators=[letters_only], blank=True)
    last_name = models.CharField(_('last name'), max_length=100, validators=[letters_only], blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_contractor = models.BooleanField(_('contractor status'), default=False)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    company_name = models.CharField(_('company name'), max_length=100, blank=True)
    
    # Campos de autenticação e segurança
    email_verified = models.BooleanField(_('email verified'), default=False)
    failed_login_attempts = models.IntegerField(_('failed login attempts'), default=0)
    last_failed_login = models.DateTimeField(_('last failed login'), null=True, blank=True)
    account_locked = models.BooleanField(_('account locked'), default=False)
    two_factor_enabled = models.BooleanField(_('two-factor authentication'), default=False)
    two_factor_secret = models.CharField(_('two-factor secret'), max_length=32, blank=True)
    
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

    # Métodos de segurança
    def lock_account(self):
        self.account_locked = True
        self.save()
        
    def unlock_account(self):
        self.account_locked = False
        self.failed_login_attempts = 0
        self.save()

    def increment_failed_login_attempts(self):
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        if self.failed_login_attempts >= 5:  # Bloqueia após 5 tentativas
            self.lock_account()
        self.save()

    def reset_failed_login_attempts(self):
        self.failed_login_attempts = 0
        self.save()

    # Métodos 2FA
    def enable_2fa(self):
        self.two_factor_enabled = True
        self.save()

    def disable_2fa(self):
        self.two_factor_enabled = False
        self.save()

    def generate_2fa_secret(self):
        self.two_factor_secret = pyotp.random_base32()
        self.save()

    def get_2fa_uri(self):
        return pyotp.totp.TOTP(self.two_factor_secret).provisioning_uri(
            name=self.email,
            issuer_name="YourAppName"
        )

    def verify_2fa(self, token):
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.verify(token)

    # Métodos de validação
    def clean(self):
        super().clean()
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
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Le numéro de téléphone doit être au format: '+999999999'.")
    )
    
    phone_number = models.CharField(
        _('phone number'), 
        max_length=15, 
        blank=True, 
        validators=[phone_regex]
    )
    
    letters_only = RegexValidator(
        regex=r'^[a-zA-ZÀ-ÿ\s\-]+$',
        message=_("Ce champ doit contenir uniquement des lettres, des espaces et des tirets.")
    )
    
    address = models.TextField(
        _('Adresse'),
        max_length=200,
        blank=True,
    )
    postal_code = models.CharField(
        _('Code Postal'), 
        max_length=10,
        blank=True,
    )
    city = models.CharField(
        _('Ville'), 
        max_length=100,
        blank=True
    )
    created_at = models.DateTimeField(
        _('date de création'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('date de mise à jour'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('profil client')
        verbose_name_plural = _('profils clients')
        

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.city}"
    
    def clean(self):
        super().clean()
        
        if self.phone_number:
            numeric_phone = ''.join(filter(str.isdigit, self.phone_number))
            if len(numeric_phone) < 10:
                raise ValidationError({'telefone': _("Le numéro de téléphone est trop court.")})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
    
class NewsletterSubscription(models.Model):
    name = models.CharField(_("nom"), max_length=100)
    email = models.EmailField(_("email"), unique=True)
    subscribed_at = models.DateTimeField(
        _("date d'inscription"), 
        default=timezone.now,  # Adicionamos um default
        editable=False  # Tornamos o campo não editável
    )
    is_active = models.BooleanField(_("actif"), default=True)

    class Meta:
        verbose_name = _("inscription newsletter")
        verbose_name_plural = _("inscriptions newsletter")

    def __str__(self):
        return f"{self.name} ({self.email})"
