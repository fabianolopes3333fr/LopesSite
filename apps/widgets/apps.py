from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WidgetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.widgets'
    verbose_name = _('Sistema de Templates')

    
    def ready(self):
        # Importa os signals
        import apps.widgets.signals