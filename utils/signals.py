# apps/config/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from apps.config.models import Page, SiteStyle, Menu

@receiver([post_save, post_delete], sender=Page)
@receiver([post_save, post_delete], sender=SiteStyle)
@receiver([post_save, post_delete], sender=Menu)
def clear_cache(sender, **kwargs):
    cache.clear()