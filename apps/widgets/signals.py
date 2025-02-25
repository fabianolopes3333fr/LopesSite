from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import (
    ComponentTemplate, 
    ComponentInstance, 
    Widget, 
    WidgetInstance,
    LayoutTemplate
)


@receiver(post_save, sender=ComponentTemplate)
def clear_component_cache(sender, instance, **kwargs):
    """
    Limpa o cache quando um template de componente é atualizado.
    """
    cache_key = f'component_{instance.slug}'
    cache.delete(cache_key)


@receiver(post_save, sender=ComponentInstance)
def clear_region_cache(sender, instance, **kwargs):
    """
    Limpa o cache quando uma instância de componente é atualizada.
    """
    region = instance.region
    cache_key = f'region_{region.template.slug}_{region.slug}'
    cache.delete(cache_key)



@receiver(post_delete, sender=ComponentInstance)
def clear_region_cache_on_delete(sender, instance, **kwargs):
    """
    Limpa o cache quando uma instância de componente é excluída.
    """
    region = instance.region
    cache_key = f'region_{region.template.slug}_{region.slug}'
    cache.delete(cache_key)


@receiver(post_save, sender=Widget)
def clear_widget_cache(sender, instance, **kwargs):
    """
    Limpa o cache quando um widget é atualizado.
    """
    cache_key = f'widget_{instance.slug}'
    cache.delete(cache_key)


@receiver(post_save, sender=WidgetInstance)
def clear_widget_area_cache(sender, instance, **kwargs):
    """
    Limpa o cache quando uma instância de widget é atualizada.
    """
    area = instance.area
    cache_key = f'widget_area_{area.template.slug}_{area.slug}'
    cache.delete(cache_key)


@receiver(post_delete, sender=WidgetInstance)
def clear_widget_area_cache_on_delete(sender, instance, **kwargs):
    """
    Limpa o cache quando uma instância de widget é excluída.
    """
    area = instance.area
    cache_key = f'widget_area_{area.template.slug}_{area.slug}'
    cache.delete(cache_key)


@receiver(post_save, sender=LayoutTemplate)
def clear_layout_cache(sender, instance, **kwargs):
    """
    Limpa o cache quando um layout é atualizado.
    """
    cache_key = f'layout_{instance.slug}'
    cache.delete(cache_key)
    
    # Se o layout for definido como padrão, limpa o cache de layout padrão
    if instance.is_default:
        cache.delete('default_layout')
# your_cms_app/templates/__init__.py

default_app_config = 'apps.widgets.apps.WidgetsConfig'