# apps/config/context_processors.py
from apps.config.models import SiteStyle, Menu

def config_context(request):
    return {
        'site_style': SiteStyle.objects.first(),
        'main_menu': Menu.objects.filter(parent=None, active=True),
    }