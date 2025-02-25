# your_cms_app/templates/templatetags/template_tags.py

from django import template
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from ..models import (
    ComponentTemplate, 
    LayoutTemplate, 
    DjangoTemplate, 
    TemplateRegion, 
    ComponentInstance,
    WidgetArea,
    WidgetInstance
)
from ..utils import (
    render_component, 
    get_component_instances_for_region, 
    get_widgets_for_area
)
import json
import re

register = template.Library()


@register.simple_tag(takes_context=True)
def render_region(context, region_slug, template_slug=None):
    """
    Renderiza uma região de template com todos os seus componentes.
    
    Uso:
    {% render_region 'content' 'home_page' %}
    """
    request = context.get('request')
    
    if not template_slug:
        # Tenta obter o template atual do contexto
        template_slug = context.get('current_template_slug')
        if not template_slug:
            return ''
    
    # Renderiza todos os componentes da região
    content = get_component_instances_for_region(region_slug, template_slug, context, request)
    return mark_safe(content)


@register.simple_tag(takes_context=True)
def render_widget_area(context, area_slug, template_slug=None):
    """
    Renderiza uma área de widgets com todos os seus widgets.
    
    Uso:
    {% render_widget_area 'sidebar' 'home_page' %}
    """
    request = context.get('request')
    
    if not template_slug:
        # Tenta obter o template atual do contexto
        template_slug = context.get('current_template_slug')
        if not template_slug:
            return ''
    
    # Renderiza todos os widgets da área
    content = get_widgets_for_area(area_slug, template_slug, context, request)
    return mark_safe(content)


@register.simple_tag
def component(component_slug, **kwargs):
    """
    Renderiza um componente específico com os parâmetros fornecidos.
    
    Uso:
    {% component 'alert' type='success' message='Operação realizada com sucesso!' %}
    """
    return mark_safe(render_component(component_slug, kwargs))


@register.inclusion_tag('components/include_component.html')
def include_component(component_slug, **kwargs):
    """
    Inclui um componente usando um template para encapsulá-lo.
    Útil quando for necessário adicionar contexto extra ou lógica adicional.
    
    Uso:
    {% include_component 'card' title='Meu Card' body='Conteúdo do card' %}
    """
    try:
        component = ComponentTemplate.objects.get(slug=component_slug, is_active=True)
        rendered_content = component.render(kwargs)
        return {
            'component': component,
            'rendered_content': rendered_content,
            'params': kwargs
        }
    except ObjectDoesNotExist:
        if settings.DEBUG:
            return {
                'error': f"Componente '{component_slug}' não encontrado"
            }
        return {
            'rendered_content': ''
        }


@register.simple_tag(takes_context=True)
def render_layout(context, layout_slug=None):
    """
    Renderiza um layout completo (template base + header + footer + sidebar).
    
    Uso:
    {% render_layout 'default' %}
    """
    request = context.get('request')
    
    if not layout_slug:
        # Usa o layout padrão se nenhum for especificado
        try:
            layout = LayoutTemplate.objects.get(is_default=True, is_active=True)
            layout_slug = layout.slug
        except ObjectDoesNotExist:
            if settings.DEBUG:
                return _("Erro: nenhum layout padrão definido.")
            return ""
    
    # Usa a função de utilitário para renderizar o layout
    from ..utils import render_layout
    return mark_safe(render_layout(layout_slug, context))


@register.simple_tag
def get_available_layouts():
    """
    Retorna todos os layouts disponíveis.
    
    Uso:
    {% get_available_layouts as layouts %}
    """
    return LayoutTemplate.objects.filter(is_active=True)


@register.filter
def json_script(value, element_id):
    """
    Similar ao filtro json_script do Django, mas permite personalizar o ID do elemento.
    
    Uso:
    {{ my_data|json_script:'my-data' }}
    """
    if value is None:
        return ''
    
    json_str = json.dumps(value)
    return mark_safe(f'<script id="{element_id}" type="application/json">{json_str}</script>')


@register.filter
def as_style(css_dict):
    """
    Converte um dicionário de propriedades CSS em uma string de estilo inline.
    
    Uso:
    {{ css_props|as_style }}
    """
    if not css_dict:
        return ''
    
    style_parts = []
    for prop, value in css_dict.items():
        # Converte camelCase para kebab-case
        kebab_prop = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', prop).lower()
        style_parts.append(f"{kebab_prop}: {value}")
    
    return '; '.join(style_parts)


@register.simple_tag
def get_template_regions(template_slug):
    """
    Retorna todas as regiões de um template específico.
    
    Uso:
    {% get_template_regions 'home_page' as regions %}
    """
    try:
        template = DjangoTemplate.objects.get(slug=template_slug)
        return template.regions.all().order_by('order')
    except ObjectDoesNotExist:
        return []


@register.simple_tag
def get_template_widget_areas(template_slug):
    """
    Retorna todas as áreas de widgets de um template específico.
    
    Uso:
    {% get_template_widget_areas 'home_page' as widget_areas %}
    """
    try:
        template = DjangoTemplate.objects.get(slug=template_slug)
        return template.widget_areas.all().order_by('order')
    except ObjectDoesNotExist:
        return []


@register.simple_tag(takes_context=True)
def editable_region(context, region_slug, template_slug=None, placeholder=None):
    """
    Renderiza uma região editável com controles de edição para o painel administrativo.
    
    Uso:
    {% editable_region 'content' placeholder='Adicione conteúdo aqui' %}
    """
    request = context.get('request')
    user = getattr(request, 'user', None)
    
    # Verifica se o usuário está no modo de edição e tem permissões
    is_edit_mode = getattr(request, 'is_edit_mode', False) and user and user.is_staff
    
    if not template_slug:
        template_slug = context.get('current_template_slug')
        if not template_slug:
            return ''
    
    # Renderiza o conteúdo da região
    content = get_component_instances_for_region(region_slug, template_slug, context, request)
    
    # No modo de edição, adiciona controles para editar a região
    if is_edit_mode:
        try:
            template = DjangoTemplate.objects.get(slug=template_slug)
            region = template.regions.get(slug=region_slug)
            
            edit_controls = render_to_string('admin/editable_region_controls.html', {
                'region': region,
                'template': template,
                'content': content,
                'placeholder': placeholder or _("Adicione componentes aqui")
            })
            
            return mark_safe(f'{edit_controls}{content}')
        except ObjectDoesNotExist:
            if settings.DEBUG:
                return mark_safe(f'<div class="error">Região "{region_slug}" não encontrada no template "{template_slug}"</div>')
    
    return mark_safe(content)


@register.simple_tag(takes_context=True)
def editable_widget_area(context, area_slug, template_slug=None, placeholder=None):
    """
    Renderiza uma área de widgets editável com controles de edição para o painel administrativo.
    
    Uso:
    {% editable_widget_area 'sidebar' placeholder='Adicione widgets aqui' %}
    """
    request = context.get('request')
    user = getattr(request, 'user', None)
    
    # Verifica se o usuário está no modo de edição e tem permissões
    is_edit_mode = getattr(request, 'is_edit_mode', False) and user and user.is_staff
    
    if not template_slug:
        template_slug = context.get('current_template_slug')
        if not template_slug:
            return ''
    
    # Renderiza o conteúdo da área de widgets
    content = get_widgets_for_area(area_slug, template_slug, context, request)
    
    # No modo de edição, adiciona controles para editar a área de widgets
    if is_edit_mode:
        try:
            template = DjangoTemplate.objects.get(slug=template_slug)
            area = template.widget_areas.get(slug=area_slug)
            
            edit_controls = render_to_string('admin/editable_widget_area_controls.html', {
                'area': area,
                'template': template,
                'content': content,
                'placeholder': placeholder or _("Adicione widgets aqui")
            })
            
            return mark_safe(f'{edit_controls}{content}')
        except ObjectDoesNotExist:
            if settings.DEBUG:
                return mark_safe(f'<div class="error">Área "{area_slug}" não encontrada no template "{template_slug}"</div>')
    
    return mark_safe(content)


@register.filter
def component_preview(component, size='md'):
    """
    Renderiza uma prévia miniatura de um componente.
    
    Uso:
    {{ component|component_preview:'sm' }}
    """
    if not isinstance(component, ComponentTemplate):
        return ''
    
    if component.thumbnail:
        if size == 'sm':
            return mark_safe(f'<img src="{component.thumbnail.url}" alt="{component.name}" class="component-preview-sm" />')
        elif size == 'lg':
            return mark_safe(f'<img src="{component.thumbnail.url}" alt="{component.name}" class="component-preview-lg" />')
        else:
            return mark_safe(f'<img src="{component.thumbnail.url}" alt="{component.name}" class="component-preview-md" />')
    
    # Se não tiver thumbnail, renderiza uma prévia usando o próprio template
    dummy_context = component.default_context or {}
    preview = component.render(dummy_context)
    
    # Limita o tamanho da prévia
    if len(preview) > 500:
        preview = preview[:500] + '...'
    
    return mark_safe(f'<div class="component-preview-code">{preview}</div>')


@register.filter
def get_css_var(variable_name, default=''):
    """
    Retorna o valor de uma variável CSS personalizada do sistema de temas.
    
    Uso:
    {{ 'primary-color'|get_css_var:'#007bff' }}
    """
    from ..models import StyleVariable
    
    try:
        var = StyleVariable.objects.get(name=variable_name, is_active=True)
        return var.value
    except ObjectDoesNotExist:
        return default