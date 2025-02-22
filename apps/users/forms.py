from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from .models import CustomUser, ClientProfile
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.conf import settings
import random
import re
from utils.email import send_new_password_email
import string


class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(
        label=_('Mot de passe'),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
    )
    password2 = forms.CharField(
        label=_('Confirmer le mot de passe'),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
    )
    
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')
        labels = {
            'email': _('E-mail'),
            'first_name': _('Prénom'),
            'last_name': _('Nom'),
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.is_authenticated:  # Corrigido is_autenticated para is_authenticated
            del self.fields['password1']
            del self.fields['password2']
            
        for field_name, field in self.fields.items():
            if field.widget.__class__ in [forms.CheckboxInput, forms.RadioSelect]:
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            if len(password1) < 8:
                raise forms.ValidationError(_('Le mot de passe doit contenir au moins 8 caractères'))
            if not re.search(r'[A-Z]', password1) or \
               not re.search(r'[a-z]', password1) or \
               not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
                raise forms.ValidationError(
                    _('Le mot de passe doit contenir au moins une majuscule, '
                      'une minuscule et un caractère spécial (!@#$%^&*(),.?":{}|<>)')
                )
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(_("Les mots de passe ne correspondent pas!"))
        return password2       
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Campos para capitalizar
        fields_to_capitalize = ['first_name', 'last_name']
        
        # Preposições e artigos em minúsculas
        lowercase_words = ['de', 'la', 'le', 'les', 'du', 'des', 'et']

        for field in fields_to_capitalize:
            if field in cleaned_data and cleaned_data[field]:
                words = cleaned_data[field].split()
                capitalized_words = []
                for i, word in enumerate(words):
                    if word.lower() not in lowercase_words:
                        capitalized_words.append(word.capitalize())
                    else:
                        capitalized_words.append(word.lower())
                cleaned_data[field] = ' '.join(capitalized_words)
        
        return cleaned_data  
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if self.user and self.user.is_authenticated:
            password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            user.set_password(password)
            user.save()
            
            # Usa a função de email centralizada
            
            send_new_password_email(user, password)
        else:
            user.set_password(self.cleaned_data.get('password1'))
        
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label=_('E-mail'),
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'class': 'form-control'
        })
    )
    password = forms.CharField(
        label=_('Mot de passe'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name')
        help_texts = {'username': None}
        labels = {
            'email': _('E-mail'),
            'first_name': _('Prénom'),
            'last_name': _('Nom'),
            'is_active': _('Utilisateur actif ?')
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and not self.user.groups.filter(
            name__in=['administrateur', 'collaborateur', 'utilisateur']
        ).exists():
            del self.fields['is_active']

        for field_name, field in self.fields.items():
            if field.widget.__class__ in [forms.CheckboxInput, forms.RadioSelect]:
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'

class TwoFactorAuthForm(forms.Form):
    token = forms.CharField(
        label=_("Entrez le code à 6 chiffres"),
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off'
        })
    )
        
class CustomUserProfileForm(forms.ModelForm):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Le numéro de téléphone doit être au format: '+999999999'. Jusqu'à 15 chiffres autorisés.")
    )

    phone_number = forms.CharField(
        validators=[phone_regex], 
        max_length=17,
        required=False
    )

    class Meta:
        model = ClientProfile
        fields = ('phone_number', 'address', 'postal_code', 'city')
        labels = {
            'phone_number': _('Numéro de téléphone'),
            'address': _('Adresse'),
            'postal_code': _('Code postal'),
            'city': _('Ville')
        }
        error_messages = {
            'phone_number': {
                'invalid': _("Veuillez entrer un numéro de téléphone valide."),
            },
            'postal_code': {
                'invalid': _("Veuillez entrer un code postal valide."),
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona classes Bootstrap aos campos
        for field_name, field in self.fields.items():
            if field.widget.__class__ in [forms.CheckboxInput, forms.RadioSelect]:
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'
                field.widget.attrs['placeholder'] = field.label

    def clean_postal_code(self):
        postal_code = self.cleaned_data.get('postal_code')
        if postal_code:
            # Formato francês de código postal: 5 dígitos
            if not postal_code.isdigit() or len(postal_code) != 5:
                raise forms.ValidationError(
                    _("Le code postal doit contenir exactement 5 chiffres.")
                )
        return postal_code

    def clean_city(self):
        city = self.cleaned_data.get('city')
        if city:
            # Lista de palavras que devem permanecer em minúsculas
            lowercase_words = ['sur', 'sous', 'les', 'la', 'le', 'en', 'de', 'du', 'des', 'et']
            
            words = city.split()
            capitalized_words = []
            
            for i, word in enumerate(words):
                word_lower = word.lower()
                if i == 0 or word_lower not in lowercase_words:
                    capitalized_words.append(word.capitalize())
                else:
                    capitalized_words.append(word_lower)
            
            return ' '.join(capitalized_words)
        return city

    def clean_address(self):
        address = self.cleaned_data.get('address')
        if address:
            # Formatação específica para endereços franceses
            address_parts = address.split(',')
            formatted_parts = []
            
            for part in address_parts:
                part = part.strip()
                if part:
                    # Capitaliza a primeira letra de cada parte do endereço
                    formatted_parts.append(part[0].upper() + part[1:].lower())
            
            return ', '.join(formatted_parts)
        return address