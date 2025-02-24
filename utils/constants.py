# apps/config/constants.py
from django.utils.translation import gettext_lazy as _

# Configurações gerais
ITEMS_PER_PAGE = 10

# Status das páginas
PAGE_STATUS = {
    'draft': _('Brouillon'),
    'published': _('Publié')
}

# Templates disponíveis
PAGE_TEMPLATES = {
    'default': _('Template par défaut'),
    'home': _('Page d\'accueil'),
    'services': _('Page de services'),
    'contact': _('Page de contact')
}

# Opções de menu
MENU_TARGET_OPTIONS = [
    ('_self', _('Même fenêtre')),
    ('_blank', _('Nouvelle fenêtre'))
]