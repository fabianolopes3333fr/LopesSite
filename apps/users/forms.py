from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, ClientProfile
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.conf import settings
import random
import re
import string


class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')
        labels = {
            'email': _('E-mail'),
            'first_name': _('Prenom'),
            'last_name': _('Nom'),
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.is_autenticated:
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
            if not re.search(r'[A-Z]', password1) or not re.search(r'[a-z]', password1) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
                raise forms.ValidationError(_('Le mot de passe doit contenir au moins une majuscule, une minuscule, un caractère spécial (!@#$%^&*(),.?":{}|<>)'))
            return password1
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(_("As senhas não são iguais!"))
        
        return password2       
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Lista de campos para capitalizar
        fields_to_capitalize = ['first_name', 'last_name']
        
        # Lista de preposições e artigos que devem permanecer em minúsculas
        lowercase_words = ['de', 'da', 'do', 'das', 'dos', 'e']

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
            send_mail(
                subject= _('Novo mot de passe'),
                message=f'Votre nouveau mot de passe est: {password}',
                from_email= settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
                
            )
                
        else:
            user.set_password(self.cleaned_data.get('password1'))
        if commit:
            user.save()
        return user      

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name')
        help_texts = {'username': None}
        labels = {
            'email': _('E-mail'),
            'first_name': _('Prenom'),
            'last_name': _('Nom'),
            'is_active': _('Utilisateur actif?')
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and not self.user.groups.filter(name__in=['administrateur', 'collaborateur', 'utilisateur']).exists():
            del self.fields['is_active']

        for field_name, field in self.fields.items():
            if field.widget.__class__ in [forms.CheckboxInput, forms.RadioSelect]:
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'
        
class CustomUserProfileForm(forms.ModelForm):
    class Meta:
        model = ClientProfile
        fields = ('phone_number', 'address', 'postal_code', 'city')
        help_texts = {'username': None}
        labels = {
            'phone_number': _('Numéro de téléphone'),
            'address': _('address')
        }
    def clean(self):
        cleaned_data = super().clean()
        
        # Lista de campos para capitalizar
        fields_to_capitalize = ['phone_number', 'address', 'postal_code', 'city']
        
        # Lista de preposições e artigos que devem permanecer em minúsculas
        lowercase_words = ['de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os']
        
        for field in fields_to_capitalize:
            if field in cleaned_data and cleaned_data[field]:
                words = cleaned_data[field].split()
                capitalized_words = []
                for i, word in enumerate(words):
                    if i == 0 or word.lower() not in lowercase_words:
                        capitalized_words.append(word.capitalize())
                    else:
                        capitalized_words.append(word.lower())
                cleaned_data[field] = ' '.join(capitalized_words)
        
        return cleaned_data