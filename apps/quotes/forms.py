from datetime import timezone
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Quote
from django.core.validators import RegexValidator

class QuoteRequestForm(forms.ModelForm):
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Le numéro de téléphone doit être au format: '+999999999'. Jusqu'à 15 chiffres autorisés.")
    )
    phone = forms.CharField(validators=[phone_regex], max_length=17)
    
    class Meta:
        model = Quote
        fields = [
            'name', 'email', 'phone', 'address', 'postal_code', 'city',
            'service_type', 'area_size', 'project_description', 'preferred_date',
            'budget_range'
        ]
        widgets = {
            
            'preferred_date': forms.DateInput(attrs={'type': 'date'}),
            'project_description': forms.Textarea(attrs={'rows': 4}),
            # 'name': forms.TextInput(attrs={
            #     'class': 'form-control',
            #     'placeholder': _('Votre nom complet')
            # }),
            # 'email': forms.EmailInput(attrs={
            #     'class': 'form-control',
            #     'placeholder': _('Votre email')
            # }),
            # 'phone': forms.TextInput(attrs={
            #     'class': 'form-control',
            #     'placeholder': _('Votre numéro de téléphone')
            # }),
            # 'address': forms.Textarea(attrs={
            #     'class': 'form-control',
            #     'rows': 3,
            #     'placeholder': _('Votre adresse complète')
            # }),
            # 'postal_code': forms.TextInput(attrs={
            #     'class': 'form-control',
            #     'placeholder': _('Code postal')
            # }),
            # 'city': forms.TextInput(attrs={
            #     'class': 'form-control',
            #     'placeholder': _('Ville')
            # }),
            # 'service_type': forms.Select(attrs={'class': 'form-select'}),
            # 'area_size': forms.NumberInput(attrs={
            #     'class': 'form-control',
            #     'placeholder': _('Surface en m²')
            # }),
            # 'project_description': forms.Textarea(attrs={
            #     'class': 'form-control',
            #     'rows': 5,
            #     'placeholder': _('Décrivez votre projet en détail')
            # }),
            # 'preferred_date': forms.DateInput(attrs={
            #     'class': 'form-control',
            #     'type': 'date'
            # }),
            # 'budget_range': forms.Select(attrs={
            #     'class': 'form-select'
            # }, choices=[
            #     ('', _('Sélectionnez une plage de budget')),
            #     ('0-1000', '0 - 1000€'),
            #     ('1000-3000', '1000 - 3000€'),
            #     ('3000-5000', '3000 - 5000€'),
            #     ('5000+', '5000€ et plus')
            # ])
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Remove todos os caracteres não numéricos
        phone = ''.join(filter(str.isdigit, phone))
        if not phone:
            raise forms.ValidationError(_('Numéro de téléphone invalide'))
        return phone

    def clean_postal_code(self):
        postal_code = self.cleaned_data.get('postal_code')
        # Validação específica para código postal francês
        if not postal_code.isdigit() or len(postal_code) != 5:
            raise forms.ValidationError(_('Code postal invalide'))
        return postal_code
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and not email.endswith(('.com', '.fr', '.org')):
            raise forms.ValidationError(_("Veuillez fournir une adresse e-mail valide."))
        return email

    def clean_preferred_date(self):
        date = self.cleaned_data.get('preferred_date')
        if date and date < timezone.now().date():
            raise forms.ValidationError(_("La date préférée ne peut pas être dans le passé."))
        return date