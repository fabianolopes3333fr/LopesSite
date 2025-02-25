# your_cms_app/templates/models.py

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.conf import settings
from colorfield.fields import ColorField
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.text import slugify
from django.urls import reverse
import json
from django.core.exceptions import ValidationError


class BaseTemplate(models.Model):
    """
    Modelo base para templates do sistema.
    Contém os campos comuns para todos os templates.
    """
    name = models.CharField(
        _('Nome'), 
        max_length=100,
        help_text=_('Nome do template')
    )
    slug = models.SlugField(
        _('Slug'), 
        max_length=100, 
        unique=True,
        help_text=_('Identificador único para o template')
    )
    description = models.TextField(
        _('Descrição'), 
        blank=True,
        help_text=_('Descrição do propósito do template')
    )
    is_active = models.BooleanField(
        _('Ativo'), 
        default=True,
        help_text=_('Define se o template está disponível para uso')
    )
    created_at = models.DateTimeField(
        _('Data de Criação'), 
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Última Atualização'), 
        auto_now=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='%(class)s_created',
        verbose_name=_('Criado por')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='%(class)s_updated',
        verbose_name=_('Atualizado por')
    )

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class TemplateCategory(BaseTemplate):
    """
    Categorias para organizar os templates.
    """
    icon = models.CharField(
        _('Ícone'), 
        max_length=50, 
        blank=True,
        help_text=_('Nome da classe do ícone (FontAwesome, Bootstrap Icons, etc.)')
    )
    parent = TreeForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='children',
        verbose_name=_('Categoria Pai')
    )

    class Meta:
        verbose_name = _('Categoria de Template')
        verbose_name_plural = _('Categorias de Templates')


class TemplateType(BaseTemplate):
    """
    Tipo de template (página completa, seção, componente, etc.)
    """
    TEMPLATE_TYPES = (
        ('page', _('Página Completa')),
        ('section', _('Seção')),
        ('header', _('Cabeçalho')),
        ('footer', _('Rodapé')),
        ('sidebar', _('Barra Lateral')),
        ('component', _('Componente')),
        ('widget', _('Widget')),
        ('custom', _('Personalizado')),
    )
    
    type = models.CharField(
        _('Tipo'), 
        max_length=20, 
        choices=TEMPLATE_TYPES,
        help_text=_('Tipo de estrutura do template')
    )
    category = models.ForeignKey(
        TemplateCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='template_types',
        verbose_name=_('Categoria')
    )
    icon = models.CharField(
        _('Ícone'), 
        max_length=50, 
        blank=True,
        help_text=_('Nome da classe do ícone (FontAwesome, Bootstrap Icons, etc.)')
    )

    class Meta:
        verbose_name = _('Tipo de Template')
        verbose_name_plural = _('Tipos de Templates')


class DjangoTemplate(BaseTemplate):
    """
    Representa um template Django físico no sistema de arquivos.
    Usado para mapear os templates do projeto.
    """
    file_path = models.CharField(
        _('Caminho do Arquivo'), 
        max_length=255,
        help_text=_('Caminho relativo ao diretório de templates')
    )
    type = models.ForeignKey(
        TemplateType, 
        on_delete=models.CASCADE,
        related_name='django_templates',
        verbose_name=_('Tipo de Template')
    )
    default_context = models.JSONField(
        _('Contexto Padrão'), 
        blank=True, 
        null=True,
        help_text=_('Variáveis de contexto padrão em formato JSON')
    )
    preview_image = models.ImageField(
        _('Imagem de Prévia'), 
        upload_to='templates/previews/', 
        blank=True, 
        null=True,
        help_text=_('Imagem de prévia do template')
    )

    class Meta:
        verbose_name = _('Template Django')
        verbose_name_plural = _('Templates Django')

    def get_absolute_url(self):
        return reverse('template_preview', kwargs={'slug': self.slug})


class TemplateRegion(models.Model):
    """
    Define uma região editável dentro de um template.
    Cada região pode conter múltiplos blocos de conteúdo.
    """
    name = models.CharField(
        _('Nome'), 
        max_length=100,
        help_text=_('Nome da região')
    )
    slug = models.SlugField(
        _('Slug'), 
        max_length=100,
        help_text=_('Identificador único da região no template')
    )
    template = models.ForeignKey(
        DjangoTemplate, 
        on_delete=models.CASCADE,
        related_name='regions',
        verbose_name=_('Template')
    )
    description = models.TextField(
        _('Descrição'), 
        blank=True,
        help_text=_('Descrição do propósito da região')
    )
    order = models.PositiveIntegerField(
        _('Ordem'), 
        default=0,
        help_text=_('Ordem de exibição da região')
    )
    is_required = models.BooleanField(
        _('Obrigatória'), 
        default=False,
        help_text=_('Define se a região é obrigatória no template')
    )
    max_blocks = models.PositiveIntegerField(
        _('Máximo de Blocos'), 
        default=0,
        help_text=_('Número máximo de blocos permitidos (0 = ilimitado)')
    )
    allowed_block_types = models.ManyToManyField(
        'ComponentTemplate',
        blank=True,
        related_name='allowed_in_regions',
        verbose_name=_('Tipos de Blocos Permitidos'),
        help_text=_('Tipos de componentes que podem ser adicionados nesta região')
    )

    class Meta:
        verbose_name = _('Região de Template')
        verbose_name_plural = _('Regiões de Templates')
        ordering = ['template', 'order']
        unique_together = ('template', 'slug')

    def __str__(self):
        return f"{self.template.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class LayoutTemplate(BaseTemplate):
    """
    Define um layout de página completo que pode ser aplicado a diferentes tipos de páginas.
    Um layout combina diferentes templates (header, footer, sidebar, etc).
    """
    template = models.ForeignKey(
        DjangoTemplate, 
        on_delete=models.CASCADE,
        related_name='layouts',
        verbose_name=_('Template Base')
    )
    header = models.ForeignKey(
        DjangoTemplate, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='layout_headers',
        verbose_name=_('Cabeçalho'),
        limit_choices_to={'type__type': 'header'}
    )
    footer = models.ForeignKey(
        DjangoTemplate, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='layout_footers',
        verbose_name=_('Rodapé'),
        limit_choices_to={'type__type': 'footer'}
    )
    sidebar = models.ForeignKey(
        DjangoTemplate, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='layout_sidebars',
        verbose_name=_('Barra Lateral'),
        limit_choices_to={'type__type': 'sidebar'}
    )
    thumbnail = models.ImageField(
        _('Miniatura'), 
        upload_to='layouts/thumbnails/',
        blank=True, 
        null=True,
        help_text=_('Imagem miniatura do layout')
    )
    css_classes = models.CharField(
        _('Classes CSS'), 
        max_length=255, 
        blank=True,
        help_text=_('Classes CSS adicionais para o layout')
    )
    is_default = models.BooleanField(
        _('Padrão'), 
        default=False,
        help_text=_('Define se este é o layout padrão')
    )

    class Meta:
        verbose_name = _('Layout')
        verbose_name_plural = _('Layouts')

    def save(self, *args, **kwargs):
        # Garante que apenas um layout seja o padrão
        if self.is_default:
            LayoutTemplate.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class ComponentTemplate(BaseTemplate):
    """
    Define um componente reutilizável que pode ser adicionado às regiões dos templates.
    """
    COMPONENT_TYPES = (
        ('card', _('Card')),
        ('slider', _('Slider')),
        ('gallery', _('Galeria')),
        ('accordion', _('Accordion')),
        ('alert', _('Alerta')),
        ('badge', _('Badge')),
        ('breadcrumb', _('Breadcrumb')),
        ('button', _('Botão')),
        ('button_group', _('Grupo de Botões')),
        ('carousel', _('Carrossel')),
        ('close_button', _('Botão de Fechar')),
        ('collapse', _('Collapse')),
        ('dropdown', _('Dropdown')),
        ('list_group', _('Grupo de Lista')),
        ('modal', _('Modal')),
        ('navbar', _('Barra de Navegação')),
        ('nav_tabs', _('Navegação e Abas')),
        ('offcanvas', _('Offcanvas')),
        ('pagination', _('Paginação')),
        ('placeholder', _('Placeholder')),
        ('popover', _('Popover')),
        ('progress', _('Barra de Progresso')),
        ('scrollspy', _('Scrollspy')),
        ('spinner', _('Spinner')),
        ('toast', _('Toast')),
        ('tooltip', _('Tooltip')),
        ('custom', _('Personalizado')),
    )
    
    component_type = models.CharField(
        _('Tipo de Componente'), 
        max_length=20, 
        choices=COMPONENT_TYPES,
        help_text=_('Tipo do componente')
    )
    template_code = models.TextField(
        _('Código do Template'), 
        blank=True,
        help_text=_('Código HTML do template do componente')
    )
    css_code = models.TextField(
        _('Código CSS'), 
        blank=True,
        help_text=_('Código CSS específico do componente')
    )
    js_code = models.TextField(
        _('Código JavaScript'), 
        blank=True,
        help_text=_('Código JavaScript específico do componente')
    )
    default_context = models.JSONField(
        _('Contexto Padrão'), 
        blank=True, 
        null=True,
        help_text=_('Variáveis de contexto padrão em formato JSON')
    )
    icon = models.CharField(
        _('Ícone'), 
        max_length=50, 
        blank=True,
        help_text=_('Nome da classe do ícone (FontAwesome, Bootstrap Icons, etc.)')
    )
    thumbnail = models.ImageField(
        _('Miniatura'), 
        upload_to='components/thumbnails/',
        blank=True, 
        null=True,
        help_text=_('Imagem miniatura do componente')
    )
    category = models.ForeignKey(
        TemplateCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='components',
        verbose_name=_('Categoria')
    )
    
    class Meta:
        verbose_name = _('Componente')
        verbose_name_plural = _('Componentes')

    def render(self, context=None):
        """
        Renderiza o componente com o contexto fornecido
        """
        from django.template import Template, Context
        
        if context is None:
            context = {}
            
        # Mescla o contexto padrão com o contexto fornecido
        if self.default_context:
            merged_context = self.default_context.copy()
            merged_context.update(context)
            context = merged_context
            
        template = Template(self.template_code)
        return template.render(Context(context))


class ComponentInstance(models.Model):
    """
    Representa uma instância de um componente em uma região específica.
    Permite configurar o componente com valores específicos.
    """
    component = models.ForeignKey(
        ComponentTemplate, 
        on_delete=models.CASCADE,
        related_name='instances',
        verbose_name=_('Componente')
    )
    region = models.ForeignKey(
        TemplateRegion, 
        on_delete=models.CASCADE,
        related_name='component_instances',
        verbose_name=_('Região')
    )
    order = models.PositiveIntegerField(
        _('Ordem'), 
        default=0,
        help_text=_('Ordem de exibição do componente na região')
    )
    context_data = models.JSONField(
        _('Dados de Contexto'), 
        blank=True, 
        null=True,
        help_text=_('Dados específicos para esta instância em formato JSON')
    )
    custom_css = models.TextField(
        _('CSS Personalizado'), 
        blank=True,
        help_text=_('CSS personalizado para esta instância do componente')
    )
    custom_classes = models.CharField(
        _('Classes CSS Personalizadas'), 
        max_length=255, 
        blank=True,
        help_text=_('Classes CSS adicionais para esta instância')
    )
    is_visible = models.BooleanField(
        _('Visível'), 
        default=True,
        help_text=_('Define se o componente está visível')
    )
    visibility_rules = models.JSONField(
        _('Regras de Visibilidade'), 
        blank=True, 
        null=True,
        help_text=_('Regras para exibição condicional (JSON)')
    )
    created_at = models.DateTimeField(
        _('Data de Criação'), 
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Última Atualização'), 
        auto_now=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='component_instances_created',
        verbose_name=_('Criado por')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='component_instances_updated',
        verbose_name=_('Atualizado por')
    )

    class Meta:
        verbose_name = _('Instância de Componente')
        verbose_name_plural = _('Instâncias de Componentes')
        ordering = ['region', 'order']
        unique_together = ('region', 'order')

    def __str__(self):
        return f"{self.component.name} em {self.region.name}"

    def should_render(self, request=None, context=None):
        """
        Verifica se o componente deve ser renderizado com base nas regras de visibilidade
        """
        if not self.is_visible:
            return False
            
        if not self.visibility_rules:
            return True
            
        # Lógica para avaliar as regras de visibilidade
        # Implementação básica, pode ser expandida conforme necessidade
        rules = self.visibility_rules
        
        # Exemplo de regra: {"device": ["mobile", "tablet"]}
        if 'device' in rules and request:
            user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
            devices = rules.get('device', [])
            
            is_mobile = any(device in user_agent for device in ['mobile', 'android', 'iphone'])
            is_tablet = any(device in user_agent for device in ['ipad', 'tablet'])
            
            if 'mobile' in devices and is_mobile:
                return True
            if 'tablet' in devices and is_tablet:
                return True
            if 'desktop' in devices and not (is_mobile or is_tablet):
                return True
            
            if devices and not any([
                'mobile' in devices and is_mobile,
                'tablet' in devices and is_tablet,
                'desktop' in devices and not (is_mobile or is_tablet)
            ]):
                return False
        
        # Exemplo de regra: {"user_auth": "authenticated"}
        if 'user_auth' in rules and request:
            auth_rule = rules.get('user_auth')
            if auth_rule == 'authenticated' and not request.user.is_authenticated:
                return False
            if auth_rule == 'anonymous' and request.user.is_authenticated:
                return False
        
        # Regras personalizadas podem ser adicionadas conforme necessário
        
        return True

    def render(self, request=None, context=None):
        """
        Renderiza a instância do componente com seu contexto específico
        """
        if not self.should_render(request, context):
            return ""
            
        if context is None:
            context = {}
            
        # Mescla o contexto específico da instância
        if self.context_data:
            merged_context = context.copy()
            merged_context.update(self.context_data)
            context = merged_context
            
        # Adiciona classes personalizadas
        context['custom_classes'] = self.custom_classes
        
        return self.component.render(context)


class WidgetArea(models.Model):
    """
    Define uma área de widgets em um template.
    As áreas de widgets são regiões especiais que podem conter múltiplos widgets.
    """
    name = models.CharField(
        _('Nome'), 
        max_length=100,
        help_text=_('Nome da área de widgets')
    )
    slug = models.SlugField(
        _('Slug'), 
        max_length=100,
        help_text=_('Identificador único da área de widgets')
    )
    description = models.TextField(
        _('Descrição'), 
        blank=True,
        help_text=_('Descrição do propósito da área de widgets')
    )
    template = models.ForeignKey(
        DjangoTemplate, 
        on_delete=models.CASCADE,
        related_name='widget_areas',
        verbose_name=_('Template')
    )
    order = models.PositiveIntegerField(
        _('Ordem'), 
        default=0,
        help_text=_('Ordem de exibição da área de widgets')
    )
    css_classes = models.CharField(
        _('Classes CSS'), 
        max_length=255, 
        blank=True,
        help_text=_('Classes CSS adicionais para a área de widgets')
    )
    max_widgets = models.PositiveIntegerField(
        _('Máximo de Widgets'), 
        default=0,
        help_text=_('Número máximo de widgets permitidos (0 = ilimitado)')
    )

    class Meta:
        verbose_name = _('Área de Widgets')
        verbose_name_plural = _('Áreas de Widgets')
        ordering = ['template', 'order']
        unique_together = ('template', 'slug')

    def __str__(self):
        return f"{self.template.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Widget(BaseTemplate):
    """
    Representa um widget que pode ser adicionado a uma área de widgets.
    """
    WIDGET_TYPES = (
        ('text', _('Texto')),
        ('html', _('HTML')),
        ('menu', _('Menu')),
        ('recent_posts', _('Posts Recentes')),
        ('categories', _('Categorias')),
        ('tags', _('Tags')),
        ('search', _('Busca')),
        ('login', _('Login')),
        ('social', _('Redes Sociais')),
        ('contact', _('Contato')),
        ('image', _('Imagem')),
        ('video', _('Vídeo')),
        ('map', _('Mapa')),
        ('form', _('Formulário')),
        ('custom', _('Personalizado')),
    )
    
    widget_type = models.CharField(
        _('Tipo de Widget'), 
        max_length=20, 
        choices=WIDGET_TYPES,
        help_text=_('Tipo do widget')
    )
    template_code = models.TextField(
        _('Código do Template'), 
        blank=True,
        help_text=_('Código HTML do template do widget')
    )
    css_code = models.TextField(
        _('Código CSS'), 
        blank=True,
        help_text=_('Código CSS específico do widget')
    )
    js_code = models.TextField(
        _('Código JavaScript'), 
        blank=True,
        help_text=_('Código JavaScript específico do widget')
    )
    default_settings = models.JSONField(
        _('Configurações Padrão'), 
        blank=True, 
        null=True,
        help_text=_('Configurações padrão em formato JSON')
    )
    icon = models.CharField(
        _('Ícone'), 
        max_length=50, 
        blank=True,
        help_text=_('Nome da classe do ícone (FontAwesome, Bootstrap Icons, etc.)')
    )
    category = models.ForeignKey(
        TemplateCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='widgets',
        verbose_name=_('Categoria')
    )

    class Meta:
        verbose_name = _('Widget')
        verbose_name_plural = _('Widgets')

    def render(self, context=None, settings=None):
        """
        Renderiza o widget com o contexto e configurações fornecidos
        """
        from django.template import Template, Context
        
        if context is None:
            context = {}
            
        if settings is None:
            settings = {}
            
        # Mescla as configurações padrão com as fornecidas
        if self.default_settings:
            merged_settings = self.default_settings.copy()
            merged_settings.update(settings)
            settings = merged_settings
            
        # Adiciona as configurações ao contexto
        context['settings'] = settings
            
        template = Template(self.template_code)
        return template.render(Context(context))


class WidgetInstance(models.Model):
    """
    Representa uma instância de um widget em uma área específica.
    Permite configurar o widget com valores específicos.
    """
    widget = models.ForeignKey(
        Widget, 
        on_delete=models.CASCADE,
        related_name='instances',
        verbose_name=_('Widget')
    )
    area = models.ForeignKey(
        WidgetArea, 
        on_delete=models.CASCADE,
        related_name='widget_instances',
        verbose_name=_('Área de Widgets')
    )
    title = models.CharField(
        _('Título'), 
        max_length=100, 
        blank=True,
        help_text=_('Título opcional para esta instância do widget')
    )
    order = models.PositiveIntegerField(
        _('Ordem'), 
        default=0,
        help_text=_('Ordem de exibição do widget na área')
    )
    widget_settings = models.JSONField(
        _('Configurações'), 
        blank=True, 
        null=True,
        help_text=_('Configurações específicas para esta instância em formato JSON')
    )
    custom_css = models.TextField(
        _('CSS Personalizado'), 
        blank=True,
        help_text=_('CSS personalizado para esta instância do widget')
    )
    custom_classes = models.CharField(
        _('Classes CSS Personalizadas'), 
        max_length=255, 
        blank=True,
        help_text=_('Classes CSS adicionais para esta instância')
    )
    is_visible = models.BooleanField(
        _('Visível'), 
        default=True,
        help_text=_('Define se o widget está visível')
    )
    visibility_rules = models.JSONField(
        _('Regras de Visibilidade'), 
        blank=True, 
        null=True,
        help_text=_('Regras para exibição condicional (JSON)')
    )
    created_at = models.DateTimeField(
        _('Data de Criação'), 
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Última Atualização'), 
        auto_now=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='widget_instances_created',
        verbose_name=_('Criado por')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='widget_instances_updated',
        verbose_name=_('Atualizado por')
    )

    class Meta:
        verbose_name = _('Instância de Widget')
        verbose_name_plural = _('Instâncias de Widgets')
        ordering = ['area', 'order']
        unique_together = ('area', 'order')

    def __str__(self):
        return f"{self.widget.name} em {self.area.name}"

    def should_render(self, request=None, context=None):
        """
        Verifica se o widget deve ser renderizado com base nas regras de visibilidade
        """
        if not self.is_visible:
            return False
            
        if not self.visibility_rules:
            return True
            
        # Lógica para avaliar as regras de visibilidade
        # Similar à implementação em ComponentInstance
        rules = self.visibility_rules
        
        # Dispositivo
        if 'device' in rules and request:
            user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
            devices = rules.get('device', [])
            
            is_mobile = any(device in user_agent for device in ['mobile', 'android', 'iphone'])
            is_tablet = any(device in user_agent for device in ['ipad', 'tablet'])
            
            if 'mobile' in devices and is_mobile:
                return True
            if 'tablet' in devices and is_tablet:
                return True
            if 'desktop' in devices and not (is_mobile or is_tablet):
                return True
            
            if devices and not any([
                'mobile' in devices and is_mobile,
                'tablet' in devices and is_tablet,
                'desktop' in devices and not (is_mobile or is_tablet)
            ]):
                return False
        
        # Autenticação de usuário
        if 'user_auth' in rules and request:
            auth_rule = rules.get('user_auth')
            if auth_rule == 'authenticated' and not request.user.is_authenticated:
                return False
            if auth_rule == 'anonymous' and request.user.is_authenticated:
                return False
        
        # Data e hora
        if 'date_range' in rules:
            from datetime import datetime
            date_range = rules.get('date_range', {})
            now = datetime.now()
            
            if 'start' in date_range:
                start = datetime.fromisoformat(date_range['start'])
                if now < start:
                    return False
                    
            if 'end' in date_range:
                end = datetime.fromisoformat(date_range['end'])
                if now > end:
                    return False
        
        return True

    def render(self, request=None, context=None):
        """
        Renderiza a instância do widget com suas configurações específicas
        """
        if not self.should_render(request, context):
            return ""
            
        if context is None:
            context = {}
        
        # Adiciona o título e as classes personalizadas ao contexto
        context['widget_title'] = self.title
        context['custom_classes'] = self.custom_classes
            
        return self.widget.render(context, self.settings)