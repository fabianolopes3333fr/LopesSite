# your_cms_app/templates/middleware.py

from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.utils import translation


class TemplateOverrideMiddleware(MiddlewareMixin):
    """
    Middleware para permitir o override de templates por usuários não-técnicos.
    
    Este middleware intercepta as requisições e modifica o mecanismo de resolução
    de templates para permitir que templates personalizados substituam os padrões.
    """
    
    def process_request(self, request):
        """
        Processa a requisição e configura o sistema de templates.
        """
        # Adiciona uma flag para permitir que views identifiquem se estão sendo renderizadas
        # em modo de edição ou visualização normal
        request.is_edit_mode = 'edit_mode' in request.GET and request.user.is_staff
        
        # Adiciona informações de preview quando necessário
        if 'preview_template' in request.GET and request.user.is_staff:
            request.preview_template = request.GET.get('preview_template')
        
        # Permite mudar o tema durante a requisição
        if 'theme' in request.GET and request.user.is_authenticated:
            request.session['active_theme'] = request.GET.get('theme')


class DynamicTemplateLoaderMiddleware(MiddlewareMixin):
    """
    Middleware para carregar templates dinâmicos do banco de dados.
    
    Este middleware modifica o mecanismo de resolução de templates do Django
    para permitir o carregamento de templates armazenados no banco de dados.
    """
    
    def process_template_response(self, request, response):
        """
        Processa a resposta do template para injetar contexto adicional.
        """
        # Somente processa responses baseadas em templates
        if hasattr(response, 'context_data'):
            # Adiciona o nome do template atual ao contexto
            if hasattr(response, 'template_name'):
                template_name = response.template_name
                if isinstance(template_name, str):
                    response.context_data['current_template'] = template_name
                elif isinstance(template_name, (list, tuple)) and template_name:
                    response.context_data['current_template'] = template_name[0]
            
            # Adiciona o modo de edição ao contexto
            response.context_data['is_edit_mode'] = getattr(request, 'is_edit_mode', False)
            
            # Adiciona informações do tema ativo
            active_theme = request.session.get('active_theme', settings.DEFAULT_THEME)
            response.context_data['active_theme'] = active_theme
        
        return response


class LayoutMiddleware(MiddlewareMixin):
    """
    Middleware para aplicar layouts dinamicamente às páginas.
    
    Este middleware permite que diferentes layouts sejam aplicados a diferentes tipos de páginas,
    com base em regras configuradas no painel administrativo.
    """
    
    def process_template_response(self, request, response):
        """
        Processa a resposta do template para aplicar o layout apropriado.
        """
        # Somente processa responses baseadas em templates
        if hasattr(response, 'context_data') and not getattr(response, 'no_layout', False):
            from .models import LayoutTemplate
            
            # Tenta encontrar o layout apropriado para esta página
            layout = None
            
            # Se um layout específico foi solicitado via GET
            if 'layout' in request.GET and request.user.is_staff:
                layout_slug = request.GET.get('layout')
                try:
                    layout = LayoutTemplate.objects.get(slug=layout_slug, is_active=True)
                except LayoutTemplate.DoesNotExist:
                    pass
            
            # Se não houver um layout específico, usa a URL para determinar o layout
            if layout is None:
                from django.urls import resolve
                try:
                    resolver_match = resolve(request.path)
                    view_name = resolver_match.view_name
                    
                    # Exemplo: Busca um layout associado a esta view específica
                    # Esta lógica pode ser expandida conforme necessário
                    from .models import LayoutAssignment
                    try:
                        assignment = LayoutAssignment.objects.get(view_name=view_name, is_active=True)
                        layout = assignment.layout
                    except (LayoutAssignment.DoesNotExist, LayoutAssignment.MultipleObjectsReturned):
                        pass
                except:
                    pass
            
            # Se ainda não tiver um layout, usa o padrão
            if layout is None:
                try:
                    layout = LayoutTemplate.objects.get(is_default=True, is_active=True)
                except (LayoutTemplate.DoesNotExist, LayoutTemplate.MultipleObjectsReturned):
                    # Se não houver um layout padrão, não aplica nenhum layout
                    return response
            
            # Aplica o layout ao template
            if layout and hasattr(response, 'template_name'):
                # Armazena o template original
                original_template = response.template_name
                
                # Define o novo template (o do layout)
                response.template_name = layout.template.file_path
                
                # Adiciona informações do layout ao contexto
                response.context_data['layout'] = layout
                response.context_data['original_template'] = original_template
                
                # Se o layout tiver um header, adiciona ao contexto
                if layout.header:
                    response.context_data['header_template'] = layout.header.file_path
                
                # Se o layout tiver um footer, adiciona ao contexto
                if layout.footer:
                    response.context_data['footer_template'] = layout.footer.file_path
                
                # Se o layout tiver uma sidebar, adiciona ao contexto
                if layout.sidebar:
                    response.context_data['sidebar_template'] = layout.sidebar.file_path
                
                # Adiciona classes CSS do layout
                response.context_data['layout_css_classes'] = layout.css_classes
        
        return response
    