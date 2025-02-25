# your_cms_app/templates/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.generic import View, TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.db import transaction
from django.db.models import Count

from .models import (
    TemplateCategory, 
    TemplateType, 
    DjangoTemplate, 
    TemplateRegion, 
    LayoutTemplate, 
    ComponentTemplate, 
    ComponentInstance,
    WidgetArea, 
    Widget, 
    WidgetInstance
)
from apps.widgets.utils import (
    render_component, 
    get_component_instances_for_region, 
    get_widgets_for_area,
    scan_template_directory,
    sync_templates_with_database
)

import json


class EditorMixin:
    """
    Mixin para adicionar o modo de edição ao request para visualização de controles de editor.
    """
    def dispatch(self, request, *args, **kwargs):
        request.is_edit_mode = True
        return super().dispatch(request, *args, **kwargs)


class TemplateListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Lista todos os templates disponíveis no sistema.
    """
    model = DjangoTemplate
    template_name = 'admin/templates/template_list.html'
    context_object_name = 'templates'
    permission_required = 'templates.view_djangotemplate'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtragem por tipo
        type_filter = self.request.GET.get('type')
        if type_filter:
            queryset = queryset.filter(type__type=type_filter)
        
        # Filtragem por categoria
        category_filter = self.request.GET.get('category')
        if category_filter:
            queryset = queryset.filter(type__category__slug=category_filter)
        
        # Filtragem por status
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['template_types'] = TemplateType.objects.all()
        context['categories'] = TemplateCategory.objects.all()
        return context


class TemplatePreviewView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Exibe uma prévia do template selecionado.
    """
    model = DjangoTemplate
    template_name = 'admin/templates/template_preview.html'
    context_object_name = 'template'
    permission_required = 'templates.view_djangotemplate'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_template_slug'] = self.object.slug
        
        # Adiciona o contexto padrão do template se existir
        if self.object.default_context:
            context.update(self.object.default_context)
        
        # Obtém as regiões do template
        context['regions'] = self.object.regions.all().order_by('order')
        
        # Obtém as áreas de widgets do template
        context['widget_areas'] = self.object.widget_areas.all().order_by('order')
        
        return context


class ComponentLibraryView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Biblioteca de componentes disponíveis no sistema.
    """
    model = ComponentTemplate
    template_name = 'admin/templates/component_library.html'
    context_object_name = 'components'
    permission_required = 'templates.view_componenttemplate'
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        
        # Filtragem por tipo
        component_type = self.request.GET.get('type')
        if component_type:
            queryset = queryset.filter(component_type=component_type)
        
        # Filtragem por categoria
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agrupa componentes por tipo
        context['component_types'] = []
        for type_choice in ComponentTemplate.COMPONENT_TYPES:
            type_code = type_choice[0]
            count = self.get_queryset().filter(component_type=type_code).count()
            if count > 0:
                context['component_types'].append({
                    'code': type_code,
                    'name': type_choice[1],
                    'count': count
                })
        
        # Obtém categorias com componentes
        context['categories'] = TemplateCategory.objects.filter(
            components__is_active=True
        ).distinct().annotate(
            component_count=Count('components')
        )
        
        return context


class ComponentPreviewView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Exibe uma prévia de um componente específico.
    """
    model = ComponentTemplate
    template_name = 'admin/templates/component_preview.html'
    context_object_name = 'component'
    permission_required = 'templates.view_componenttemplate'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Usa o contexto padrão do componente para a prévia
        context['preview_context'] = self.object.default_context or {}
        
        # Renderiza o componente com o contexto padrão
        context['rendered_component'] = self.object.render(context['preview_context'])
        
        return context


class LayoutEditorView(LoginRequiredMixin, PermissionRequiredMixin, EditorMixin, DetailView):
    """
    Editor visual para layouts de página.
    """
    model = LayoutTemplate
    template_name = 'admin/templates/layout_editor.html'
    context_object_name = 'layout'
    permission_required = 'templates.change_layouttemplate'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Adiciona templates disponíveis para cada parte do layout
        context['available_templates'] = DjangoTemplate.objects.filter(is_active=True)
        context['available_headers'] = DjangoTemplate.objects.filter(
            is_active=True, 
            type__type='header'
        )
        context['available_footers'] = DjangoTemplate.objects.filter(
            is_active=True, 
            type__type='footer'
        )
        context['available_sidebars'] = DjangoTemplate.objects.filter(
            is_active=True, 
            type__type='sidebar'
        )
        
        return context


class RegionEditorView(LoginRequiredMixin, PermissionRequiredMixin, EditorMixin, DetailView):
    """
    Editor visual para regiões de template.
    """
    model = TemplateRegion
    template_name = 'admin/templates/region_editor.html'
    context_object_name = 'region'
    permission_required = 'templates.change_templateregion'
    
    def get_object(self, queryset=None):
        template_slug = self.kwargs.get('template_slug')
        region_slug = self.kwargs.get('region_slug')
        
        template = get_object_or_404(DjangoTemplate, slug=template_slug)
        return get_object_or_404(TemplateRegion, template=template, slug=region_slug)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtém os componentes da região na ordem correta
        context['component_instances'] = ComponentInstance.objects.filter(
            region=self.object
        ).select_related('component').order_by('order')
        
        # Adiciona componentes disponíveis para adicionar à região
        if self.object.allowed_block_types.exists():
            # Se houver tipos permitidos especificados, usa apenas esses
            context['available_components'] = self.object.allowed_block_types.filter(is_active=True)
        else:
            # Caso contrário, mostra todos os componentes ativos
            context['available_components'] = ComponentTemplate.objects.filter(is_active=True)
        
        # Adiciona o contexto do template pai
        context['template'] = self.object.template
        context['current_template_slug'] = self.object.template.slug
        
        return context


class WidgetAreaEditorView(LoginRequiredMixin, PermissionRequiredMixin, EditorMixin, DetailView):
    """
    Editor visual para áreas de widgets.
    """
    model = WidgetArea
    template_name = 'admin/templates/widget_area_editor.html'
    context_object_name = 'widget_area'
    permission_required = 'templates.change_widgetarea'
    
    def get_object(self, queryset=None):
        template_slug = self.kwargs.get('template_slug')
        area_slug = self.kwargs.get('area_slug')
        
        template = get_object_or_404(DjangoTemplate, slug=template_slug)
        return get_object_or_404(WidgetArea, template=template, slug=area_slug)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtém os widgets da área na ordem correta
        context['widget_instances'] = WidgetInstance.objects.filter(
            area=self.object
        ).select_related('widget').order_by('order')
        
        # Adiciona widgets disponíveis para adicionar à área
        context['available_widgets'] = Widget.objects.filter(is_active=True)
        
        # Adiciona o contexto do template pai
        context['template'] = self.object.template
        context['current_template_slug'] = self.object.template.slug
        
        return context


class TemplateScanView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """
    Escaneia o sistema de arquivos para encontrar novos templates.
    """
    template_name = 'admin/templates/template_scan.html'
    permission_required = 'templates.add_djangotemplate'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['discovered_templates'] = scan_template_directory()
        return context
    
    def post(self, request, *args, **kwargs):
        if 'sync_templates' in request.POST:
            try:
                sync_templates_with_database()
                messages.success(request, _('Templates sincronizados com sucesso!'))
            except Exception as e:
                messages.error(request, _('Erro ao sincronizar templates: {}').format(str(e)))
        
        return redirect('template_scan')


@require_POST
@csrf_protect
def add_component_to_region(request, template_slug, region_slug):
    """
    Adiciona um componente a uma região via AJAX.
    """
    if not request.user.has_perm('templates.add_componentinstance'):
        return JsonResponse({'error': _('Permissão negada')}, status=403)
    
    try:
        template = DjangoTemplate.objects.get(slug=template_slug)
        region = TemplateRegion.objects.get(template=template, slug=region_slug)
        
        component_slug = request.POST.get('component_slug')
        component = ComponentTemplate.objects.get(slug=component_slug, is_active=True)
        
        # Verifica se o componente é permitido nesta região
        if region.allowed_block_types.exists() and not region.allowed_block_types.filter(id=component.id).exists():
            return JsonResponse({'error': _('Este componente não é permitido nesta região')}, status=400)
        
        # Verifica limite de componentes na região
        if region.max_blocks > 0:
            current_count = ComponentInstance.objects.filter(region=region).count()
            if current_count >= region.max_blocks:
                return JsonResponse({'error': _('Número máximo de componentes atingido')}, status=400)
        
        # Obtém a próxima ordem disponível
        order = 0
        last_instance = ComponentInstance.objects.filter(region=region).order_by('-order').first()
        if last_instance:
            order = last_instance.order + 1
        
        # Cria a instância do componente
        instance = ComponentInstance.objects.create(
            component=component,
            region=region,
            order=order,
            context_data=component.default_context,
            created_by=request.user,
            updated_by=request.user
        )
        
        # Renderiza a instância para retornar ao cliente
        rendered_component = instance.render(request)
        
        return JsonResponse({
            'success': True,
            'instance_id': instance.id,
            'rendered_component': rendered_component,
            'message': _('Componente adicionado com sucesso')
        })
        
    except (DjangoTemplate.DoesNotExist, TemplateRegion.DoesNotExist, ComponentTemplate.DoesNotExist) as e:
        return JsonResponse({'error': str(e)}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@csrf_protect
def update_component_instance(request, instance_id):
    """
    Atualiza uma instância de componente via AJAX.
    """
    if not request.user.has_perm('templates.change_componentinstance'):
        return JsonResponse({'error': _('Permissão negada')}, status=403)
    
    try:
        instance = ComponentInstance.objects.get(id=instance_id)
        
        # Atualiza os dados de contexto
        context_data = request.POST.get('context_data')
        if context_data:
            instance.context_data = json.loads(context_data)
        
        # Atualiza CSS personalizado
        custom_css = request.POST.get('custom_css')
        if custom_css is not None:
            instance.custom_css = custom_css
        
        # Atualiza classes CSS personalizadas
        custom_classes = request.POST.get('custom_classes')
        if custom_classes is not None:
            instance.custom_classes = custom_classes
        
        # Atualiza visibilidade
        is_visible = request.POST.get('is_visible')
        if is_visible is not None:
            instance.is_visible = is_visible.lower() == 'true'
        
        # Atualiza regras de visibilidade
        visibility_rules = request.POST.get('visibility_rules')
        if visibility_rules:
            instance.visibility_rules = json.loads(visibility_rules)
        
        instance.updated_by = request.user
        instance.save()
        
        # Renderiza a instância atualizada
        rendered_component = instance.render(request)
        
        return JsonResponse({
            'success': True,
            'rendered_component': rendered_component,
            'message': _('Componente atualizado com sucesso')
        })
        
    except ComponentInstance.DoesNotExist:
        return JsonResponse({'error': _('Instância do componente não encontrada')}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': _('Dados JSON inválidos')}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@csrf_protect
def reorder_components(request, template_slug, region_slug):
    """
    Reordena componentes em uma região via AJAX.
    """
    if not request.user.has_perm('templates.change_componentinstance'):
        return JsonResponse({'error': _('Permissão negada')}, status=403)
    
    try:
        template = DjangoTemplate.objects.get(slug=template_slug)
        region = TemplateRegion.objects.get(template=template, slug=region_slug)
        
        # Obtém a nova ordem dos IDs de componentes
        order_data = json.loads(request.body)
        component_ids = order_data.get('component_ids', [])
        
        if not component_ids:
            return JsonResponse({'error': _('Nenhum dado de ordenação fornecido')}, status=400)
        
        # Verifica se todos os componentes pertencem à região
        components = ComponentInstance.objects.filter(id__in=component_ids, region=region)
        if len(components) != len(component_ids):
            return JsonResponse({'error': _('Alguns componentes não foram encontrados na região')}, status=400)
        
        # Atualiza a ordem dos componentes
        with transaction.atomic():
            for index, component_id in enumerate(component_ids):
                ComponentInstance.objects.filter(id=component_id, region=region).update(
                    order=index,
                    updated_by=request.user
                )
        
        return JsonResponse({
            'success': True,
            'message': _('Ordem dos componentes atualizada com sucesso')
        })
        
    except (DjangoTemplate.DoesNotExist, TemplateRegion.DoesNotExist):
        return JsonResponse({'error': _('Template ou região não encontrados')}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': _('Dados JSON inválidos')}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@csrf_protect
def delete_component_instance(request, instance_id):
    """
    Remove uma instância de componente via AJAX.
    """
    if not request.user.has_perm('templates.delete_componentinstance'):
        return JsonResponse({'error': _('Permissão negada')}, status=403)
    
    try:
        instance = ComponentInstance.objects.get(id=instance_id)
        region = instance.region
        
        # Remove a instância
        instance.delete()
        
        # Reordena os componentes restantes
        remaining_instances = ComponentInstance.objects.filter(region=region).order_by('order')
        for index, remaining in enumerate(remaining_instances):
            remaining.order = index
            remaining.save()
        
        return JsonResponse({
            'success': True,
            'message': _('Componente removido com sucesso')
        })
        
    except ComponentInstance.DoesNotExist:
        return JsonResponse({'error': _('Instância do componente não encontrada')}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@csrf_protect
def add_widget_to_area(request, template_slug, area_slug):
    """
    Adiciona um widget a uma área de widgets via AJAX.
    """
    if not request.user.has_perm('templates.add_widgetinstance'):
        return JsonResponse({'error': _('Permissão negada')}, status=403)
    
    try:
        template = DjangoTemplate.objects.get(slug=template_slug)
        area = WidgetArea.objects.get(template=template, slug=area_slug)
        
        widget_slug = request.POST.get('widget_slug')
        widget = Widget.objects.get(slug=widget_slug, is_active=True)
        
        # Verifica limite de widgets na área
        if area.max_widgets > 0:
            current_count = WidgetInstance.objects.filter(area=area).count()
            if current_count >= area.max_widgets:
                return JsonResponse({'error': _('Número máximo de widgets atingido')}, status=400)
        
        # Obtém a próxima ordem disponível
        order = 0
        last_instance = WidgetInstance.objects.filter(area=area).order_by('-order').first()
        if last_instance:
            order = last_instance.order + 1
        
        # Obtém o título do widget (opcional)
        title = request.POST.get('title', widget.name)
        
        # Cria a instância do widget
        instance = WidgetInstance.objects.create(
            widget=widget,
            area=area,
            title=title,
            order=order,
            settings=widget.default_settings,
            created_by=request.user,
            updated_by=request.user
        )
        
        # Renderiza a instância para retornar ao cliente
        rendered_widget = instance.render(request)
        
        return JsonResponse({
            'success': True,
            'instance_id': instance.id,
            'rendered_widget': rendered_widget,
            'message': _('Widget adicionado com sucesso')
        })
        
    except (DjangoTemplate.DoesNotExist, WidgetArea.DoesNotExist, Widget.DoesNotExist) as e:
        return JsonResponse({'error': str(e)}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@csrf_protect
def update_widget_instance(request, instance_id):
    """
    Atualiza uma instância de widget via AJAX.
    """
    if not request.user.has_perm('templates.change_widgetinstance'):
        return JsonResponse({'error': _('Permissão negada')}, status=403)
    
    try:
        instance = WidgetInstance.objects.get(id=instance_id)
        
        # Atualiza o título
        title = request.POST.get('title')
        if title is not None:
            instance.title = title
        
        # Atualiza as configurações
        settings = request.POST.get('settings')
        if settings:
            instance.settings = json.loads(settings)
        
        # Atualiza CSS personalizado
        custom_css = request.POST.get('custom_css')
        if custom_css is not None:
            instance.custom_css = custom_css
        
        # Atualiza classes CSS personalizadas
        custom_classes = request.POST.get('custom_classes')
        if custom_classes is not None:
            instance.custom_classes = custom_classes
        
        # Atualiza visibilidade
        is_visible = request.POST.get('is_visible')
        if is_visible is not None:
            instance.is_visible = is_visible.lower() == 'true'
        
        # Atualiza regras de visibilidade
        visibility_rules = request.POST.get('visibility_rules')
        if visibility_rules:
            instance.visibility_rules = json.loads(visibility_rules)
        
        instance.updated_by = request.user
        instance.save()
        
        # Renderiza a instância atualizada
        rendered_widget = instance.render(request)
        
        return JsonResponse({
            'success': True,
            'rendered_widget': rendered_widget,
            'message': _('Widget atualizado com sucesso')
        })
        
    except WidgetInstance.DoesNotExist:
        return JsonResponse({'error': _('Instância do widget não encontrada')}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': _('Dados JSON inválidos')}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@csrf_protect
def reorder_widgets(request, template_slug, area_slug):
    """
    Reordena widgets em uma área de widgets via AJAX.
    """
    if not request.user.has_perm('templates.change_widgetinstance'):
        return JsonResponse({'error': _('Permissão negada')}, status=403)
    
    try:
        template = DjangoTemplate.objects.get(slug=template_slug)
        area = WidgetArea.objects.get(template=template, slug=area_slug)
        
        # Obtém a nova ordem dos IDs de widgets
        order_data = json.loads(request.body)
        widget_ids = order_data.get('widget_ids', [])
        
        if not widget_ids:
            return JsonResponse({'error': _('Nenhum dado de ordenação fornecido')}, status=400)
        
        # Verifica se todos os widgets pertencem à área
        widgets = WidgetInstance.objects.filter(id__in=widget_ids, area=area)
        if len(widgets) != len(widget_ids):
            return JsonResponse({'error': _('Alguns widgets não foram encontrados na área')}, status=400)
        
        # Atualiza a ordem dos widgets
        with transaction.atomic():
            for index, widget_id in enumerate(widget_ids):
                WidgetInstance.objects.filter(id=widget_id, area=area).update(
                    order=index,
                    updated_by=request.user
                )
        
        return JsonResponse({
            'success': True,
            'message': _('Ordem dos widgets atualizada com sucesso')
        })
        
    except (DjangoTemplate.DoesNotExist, WidgetArea.DoesNotExist):
        return JsonResponse({'error': _('Template ou área de widgets não encontrados')}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': _('Dados JSON inválidos')}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@csrf_protect
def delete_widget_instance(request, instance_id):
    """
    Remove uma instância de widget via AJAX.
    """
    if not request.user.has_perm('templates.delete_widgetinstance'):
        return JsonResponse({'error': _('Permissão negada')}, status=403)
    
    try:
        instance = WidgetInstance.objects.get(id=instance_id)
        area = instance.area
        
        # Remove a instância
        instance.delete()
        
        # Reordena os widgets restantes
        remaining_instances = WidgetInstance.objects.filter(area=area).order_by('order')
        for index, remaining in enumerate(remaining_instances):
            remaining.order = index
            remaining.save()
        
        return JsonResponse({
            'success': True,
            'message': _('Widget removido com sucesso')
        })
        
    except WidgetInstance.DoesNotExist:
        return JsonResponse({'error': _('Instância do widget não encontrada')}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class LayoutPreviewView(DetailView):
    """
    Exibe uma prévia de um layout completo.
    """
    model = LayoutTemplate
    template_name = 'templates/layout_preview.html'
    context_object_name = 'layout'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Renderiza cada parte do layout
        template = self.object.template
        context['current_template_slug'] = template.slug
        
        # Adiciona o contexto padrão do template base
        if template.default_context:
            context.update(template.default_context)
        
        # Adiciona informações do header
        if self.object.header:
            context['header_template'] = self.object.header
            context['header_slug'] = self.object.header.slug
        
        # Adiciona informações do footer
        if self.object.footer:
            context['footer_template'] = self.object.footer
            context['footer_slug'] = self.object.footer.slug
        
        # Adiciona informações da sidebar
        if self.object.sidebar:
            context['sidebar_template'] = self.object.sidebar
            context['sidebar_slug'] = self.object.sidebar.slug
        
        # Adiciona classes CSS do layout
        context['layout_css_classes'] = self.object.css_classes
        
        return context