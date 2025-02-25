# your_cms_app/templates/utils.py

from django.template import loader, Context
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ImproperlyConfigured
import os
import json
import re
from .models import (
    DjangoTemplate, 
    LayoutTemplate, 
    ComponentTemplate, 
    ComponentInstance, 
    WidgetArea, 
    WidgetInstance
)


def get_template_choices():
    """
    Retorna uma lista de templates disponíveis no projeto.
    Usado em formulários e interfaces administrativas.
    """
    template_dirs = settings.TEMPLATES[0]['DIRS']
    templates = []
    
    for template_dir in template_dirs:
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                if file.endswith('.html'):
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, template_dir)
                    templates.append((rel_path, rel_path))
    
    return sorted(templates)


def extract_blocks_from_template(template_path):
    """
    Extrai os blocos definidos em um arquivo de template.
    Útil para identificar regiões personalizáveis.
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
        blocks = re.findall(block_pattern, content)
        
        return list(set(blocks))
    except FileNotFoundError:
        return []


def render_layout(layout_slug, context=None):
    """
    Renderiza um layout completo com suas partes (header, footer, sidebar).
    """
    if context is None:
        context = {}

    try:
        layout = LayoutTemplate.objects.get(slug=layout_slug, is_active=True)
    except LayoutTemplate.DoesNotExist:
        if settings.DEBUG:
            raise ImproperlyConfigured(f"Layout '{layout_slug}' não encontrado")
        layout = LayoutTemplate.objects.filter(is_default=True, is_active=True).first()
        if not layout:
            raise ImproperlyConfigured("Nenhum layout padrão ativo encontrado")
    
    # Prepara o contexto com os templates
    layout_context = context.copy()
    layout_context['base_template'] = layout.template.file_path
    
    if layout.header:
        layout_context['header_template'] = layout.header.file_path
    
    if layout.footer:
        layout_context['footer_template'] = layout.footer.file_path
        
    if layout.sidebar:
        layout_context['sidebar_template'] = layout.sidebar.file_path
    
    # Adiciona classes CSS do layout
    layout_context['layout_css_classes'] = layout.css_classes
    
    # Renderiza o layout
    template = loader.get_template(layout.template.file_path)
    return template.render(layout_context)


def get_component_instances_for_region(region_slug, template_slug, context=None, request=None):
    """
    Obtém e renderiza todas as instâncias de componentes para uma região específica.
    """
    if context is None:
        context = {}
    
    try:
        template = DjangoTemplate.objects.get(slug=template_slug, is_active=True)
        region = template.regions.get(slug=region_slug)
    except (DjangoTemplate.DoesNotExist, TemplateRegion.DoesNotExist):
        if settings.DEBUG:
            raise ImproperlyConfigured(f"Template '{template_slug}' ou região '{region_slug}' não encontrados")
        return ""
    
    # Obtém as instâncias de componentes para esta região, na ordem correta
    instances = ComponentInstance.objects.filter(
        region=region, 
        is_visible=True
    ).select_related('component').order_by('order')
    
    rendered_components = []
    for instance in instances:
        rendered = instance.render(request, context)
        if rendered:
            rendered_components.append(rendered)
    
    return "".join(rendered_components)


def get_widgets_for_area(area_slug, template_slug, context=None, request=None):
    """
    Obtém e renderiza todos os widgets para uma área específica.
    """
    if context is None:
        context = {}
    
    try:
        template = DjangoTemplate.objects.get(slug=template_slug, is_active=True)
        area = template.widget_areas.get(slug=area_slug)
    except (DjangoTemplate.DoesNotExist, WidgetArea.DoesNotExist):
        if settings.DEBUG:
            raise ImproperlyConfigured(f"Template '{template_slug}' ou área '{area_slug}' não encontrados")
        return ""
    
    # Obtém as instâncias de widgets para esta área, na ordem correta
    instances = WidgetInstance.objects.filter(
        area=area, 
        is_visible=True
    ).select_related('widget').order_by('order')
    
    rendered_widgets = []
    for instance in instances:
        rendered = instance.render(request, context)
        if rendered:
            rendered_widgets.append(rendered)
    
    return "".join(rendered_widgets)


def render_component(component_slug, context=None):
    """
    Renderiza um componente específico com o contexto fornecido.
    Útil para renderização programática de componentes.
    """
    if context is None:
        context = {}
    
    try:
        component = ComponentTemplate.objects.get(slug=component_slug, is_active=True)
    except ComponentTemplate.DoesNotExist:
        if settings.DEBUG:
            raise ImproperlyConfigured(f"Componente '{component_slug}' não encontrado")
        return ""
    
    return component.render(context)


def get_available_components(category=None, component_type=None):
    """
    Retorna uma lista de componentes disponíveis, opcionalmente filtrados por categoria ou tipo.
    """
    components = ComponentTemplate.objects.filter(is_active=True)
    
    if category:
        components = components.filter(category__slug=category)
    
    if component_type:
        components = components.filter(component_type=component_type)
    
    return components


def scan_template_directory():
    """
    Escaneia o diretório de templates e detecta arquivos de template disponíveis.
    Útil para sincronizar os templates do sistema de arquivos com o banco de dados.
    """
    template_dirs = settings.TEMPLATES[0]['DIRS']
    discovered_templates = []
    
    for template_dir in template_dirs:
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                if file.endswith('.html'):
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, template_dir)
                    
                    # Analisa o conteúdo do arquivo para encontrar comentários especiais
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Procura por comentários de metadados no formato: 
                    # <!-- template-meta: {"name": "Nome do Template", "type": "page", "description": "Descrição"} -->
                    meta_pattern = r'<!--\s*template-meta:\s*({[^}]+})\s*-->'
                    match = re.search(meta_pattern, content)
                    
                    metadata = {}
                    if match:
                        try:
                            metadata = json.loads(match.group(1))
                        except json.JSONDecodeError:
                            pass
                    
                    template_name = metadata.get('name', os.path.splitext(file)[0].replace('_', ' ').title())
                    template_type = metadata.get('type', 'page')
                    template_description = metadata.get('description', '')
                    
                    discovered_templates.append({
                        'path': rel_path,
                        'name': template_name,
                        'type': template_type,
                        'description': template_description
                    })
    
    return discovered_templates


def sync_templates_with_database():
    """
    Sincroniza os templates descobertos no sistema de arquivos com o banco de dados.
    """
    from django.db import transaction
    from .models import TemplateType
    
    discovered_templates = scan_template_directory()
    
    with transaction.atomic():
        for template_data in discovered_templates:
            # Obtém ou cria o tipo de template
            template_type, _ = TemplateType.objects.get_or_create(
                type=template_data['type'],
                defaults={
                    'name': template_data['type'].capitalize(),
                    'slug': template_data['type'],
                    'description': f"Tipo de template: {template_data['type']}"
                }
            )
            
            # Verifica se o template já existe no banco de dados
            template, created = DjangoTemplate.objects.get_or_create(
                file_path=template_data['path'],
                defaults={
                    'name': template_data['name'],
                    'slug': slugify(template_data['name']),
                    'description': template_data['description'],
                    'type': template_type,
                }
            )
            
            if not created:
                # Atualiza os campos do template existente
                template.name = template_data['name']
                template.description = template_data['description']
                template.type = template_type
                template.save()