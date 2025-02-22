# utils/validators.py
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

def validate_password_strength(password):
    """
    Valida a força da senha usando critérios específicos
    """
    if len(password) < 8:
        raise ValidationError(_("Le mot de passe doit contenir au moins 8 caractères."))
    
    if not any(char.isdigit() for char in password):
        raise ValidationError(_("Le mot de passe doit contenir au moins un chiffre."))
    
    if not any(char.isupper() for char in password):
        raise ValidationError(_("Le mot de passe doit contenir au moins une majuscule."))
    
    if not any(char.islower() for char in password):
        raise ValidationError(_("Le mot de passe doit contenir au moins une minuscule."))
    
    if not any(char in "!@#$%^&*()+" for char in password):
        raise ValidationError(_("Le mot de passe doit contenir au moins un caractère spécial (!@#$%^&*())."))