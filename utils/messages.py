# apps/config/messages.py
from django.utils.translation import gettext_lazy as _

MESSAGES = {
    'success': {
        'page_created': _('Page créée avec succès.'),
        'page_updated': _('Page mise à jour avec succès.'),
        'page_deleted': _('Page supprimée avec succès.'),
        'style_created': _('Style créé avec succès.'),
        'style_updated': _('Style mis à jour avec succès.'),
        'style_deleted': _('Style supprimé avec succès.'),
        'menu_created': _('Menu créé avec succès.'),
        'menu_updated': _('Menu mis à jour avec succès.'),
        'menu_deleted': _('Menu supprimé avec succès.'),
    },
    'error': {
        'invalid_css': _('CSS invalide: {}'),
        'general_error': _('Une erreur s\'est produite. Veuillez réessayer.'),
    }
}