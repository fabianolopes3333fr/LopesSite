from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(_('phone number'), max_length=15, blank=True)
    address = models.CharField(_('address'), max_length=255, blank=True)

    # Campos adicionais específicos para o seu negócio de pintura
    is_contractor = models.BooleanField(_('contractor status'), default=False)
    company_name = models.CharField(_('company name'), max_length=100, blank=True)

    # Use o email como nome de usuário
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email
