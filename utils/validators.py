# utils/validators.py
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re

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
    
    
def validate_css(css_string):
    """Validação básica de CSS"""
    try:
        # Verificar se há chaves não fechadas
        if css_string.count('{') != css_string.count('}'):
            raise ValidationError(_('CSS invalide: accolades non correspondantes'))
        
        # Verificar sintaxe básica usando regex
        css_rule_pattern = r'([^{]+){([^}]*)}'
        rules = re.findall(css_rule_pattern, css_string)
        
        if not rules and css_string.strip():
            raise ValidationError(_('CSS invalide: aucune règle valide trouvée'))
            
        return True
    except Exception as e:
        raise ValidationError(f'CSS invalide: {str(e)}')