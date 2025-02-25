from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.sites.models import Site
from django.core.validators import FileExtensionValidator
from mptt.models import MPTTModel, TreeForeignKey
from django_ckeditor_5.fields import CKEditor5Field
from colorfield.fields import ColorField
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import json
import uuid
import os

# class ContentBlock(models.Model):
#     name = models.CharField(max_length=100)
#     content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
#     object_id = models.PositiveIntegerField()
#     content_object = GenericForeignKey('content_type', 'object_id')
#     order = models.PositiveIntegerField(default=0)

#     class Meta:
#         ordering = ['order']

# class TextBlock(models.Model):
#     content = models.TextField()

# class ImageBlock(models.Model):
#     image = models.ImageField(upload_to='content_blocks/')
#     caption = models.CharField(max_length=255, blank=True)

# TEMPLATE_CHOICES = [
#     ('default', 'Default'),
#     ('homepage', 'Homepage'),
#     ('sidebar', 'With Sidebar'),
# ]
# class PagePages(models.Model):
#     title = models.CharField(max_length=200)
#     slug = models.SlugField(unique=True)
#     template = models.CharField(max_length=100, choices=TEMPLATE_CHOICES)

# class Region(models.Model):
#     page = models.ForeignKey(PagePages, on_delete=models.CASCADE, related_name='regions')
#     name = models.CharField(max_length=100)
#     content = models.TextField(blank=True)

# class TemplateOverride(models.Model):
#     name = models.CharField(max_length=100)
#     content = models.TextField()
#     is_active = models.BooleanField(default=True)

# class TemplateLoader:
#     @staticmethod
#     def get_template(name):
#         try:
#             override = TemplateOverride.objects.get(name=name, is_active=True)
#             return Template(override.content)
#         except TemplateOverride.DoesNotExist:
#             return get_template(name)

#     def get_template_sources(self, template_name, template_dirs=None):
#         try:
#             page = PagePages.objects.get(slug=template_name)
#             if page.template_content:
#                 return [{'name': template_name, 'content': page.template_content}]
#         except PagePages.DoesNotExist:
#             pass
#         return super().get_template_sources(template_name, template_dirs)
    
    
    # Novo modelo apartir deste ponto
    
    
def validate_json(value):
    """Validador para campos JSON"""
    try:
        if value:
            json.loads(value)
    except json.JSONDecodeError:
        raise ValidationError(_("O formato JSON é inválido"))


def page_image_path(instance, filename):
    """Define o caminho para imagens de página"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"pages/{instance.id}/{filename}"


def page_file_path(instance, filename):
    """Define o caminho para arquivos de página"""
    return f"pages/{instance.id}/files/{filename}"


class PageCategory(MPTTModel):
    """
    Categorias para organizar páginas de forma hierárquica
    """
    name = models.CharField(_('Nome'), max_length=100)
    slug = models.SlugField(_('Slug'), max_length=120, unique=True)
    description = models.TextField(_('Descrição'), blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                          related_name='children', verbose_name=_('Categoria pai'))
    icon = models.CharField(_('Ícone'), max_length=50, blank=True, 
                          help_text=_('Nome do ícone FontAwesome ou outro framework de ícones'))
    color = ColorField(_('Cor'), blank=True, default='#FFFFFF')
    is_active = models.BooleanField(_('Ativo'), default=True)
    order = models.IntegerField(_('Ordem'), default=0)
    created_at = models.DateTimeField(_('Data de criação'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Última atualização'), auto_now=True)

    class Meta:
        verbose_name = _('Categoria de página')
        verbose_name_plural = _('Categorias de páginas')
        ordering = ['order', 'name']

    class MPTTMeta:
        order_insertion_by = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PageTemplate(models.Model):
    """
    Templates que definem o layout e campos disponíveis para páginas
    """
    LAYOUT_CHOICES = (
        ('default', _('Padrão')),
        ('full_width', _('Largura Total')),
        ('sidebar_left', _('Barra Lateral Esquerda')),
        ('sidebar_right', _('Barra Lateral Direita')),
        ('landing', _('Landing Page')),
        ('dashboard', _('Dashboard')),
    )
    
    name = models.CharField(_('Nome'), max_length=100)
    slug = models.SlugField(_('Slug'), max_length=120, unique=True)
    description = models.TextField(_('Descrição'), blank=True)
    layout = models.CharField(_('Layout'), max_length=30, choices=LAYOUT_CHOICES, default='default')
    template_file = models.CharField(_('Arquivo de template'), max_length=200, 
                                  help_text=_('Caminho relativo para o arquivo de template'))
    preview_image = models.ImageField(_('Imagem de prévia'), upload_to='templates/previews/', blank=True, null=True)
    is_active = models.BooleanField(_('Ativo'), default=True)
    created_at = models.DateTimeField(_('Data de criação'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Última atualização'), auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='templates_created', verbose_name=_('Criado por'))
    
    class Meta:
        verbose_name = _('Template de página')
        verbose_name_plural = _('Templates de página')
        ordering = ['name']
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class FieldGroup(models.Model):
    """
    Grupos de campos para organizar campos personalizáveis em templates
    """
    name = models.CharField(_('Nome'), max_length=100)
    slug = models.SlugField(_('Slug'), max_length=120)
    description = models.TextField(_('Descrição'), blank=True)
    template = models.ForeignKey(PageTemplate, on_delete=models.CASCADE, 
                               related_name='field_groups', verbose_name=_('Template'))
    order = models.IntegerField(_('Ordem'), default=0)
    is_collapsible = models.BooleanField(_('Expansível/Retrátil'), default=True)
    is_collapsed = models.BooleanField(_('Iniciar retraído'), default=False)
    
    class Meta:
        verbose_name = _('Grupo de campos')
        verbose_name_plural = _('Grupos de campos')
        ordering = ['template', 'order', 'name']
        unique_together = ('template', 'slug')
    
    def __str__(self):
        return f"{self.template.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class FieldDefinition(models.Model):
    """
    Definição de campos personalizáveis para templates de página
    """
    FIELD_TYPES = (
        ('text', _('Texto curto')),
        ('textarea', _('Texto longo')),
        ('richtext', _('Editor rico (WYSIWYG)')),
        ('email', _('E-mail')),
        ('url', _('URL')),
        ('integer', _('Número inteiro')),
        ('decimal', _('Número decimal')),
        ('boolean', _('Checkbox (Sim/Não)')),
        ('date', _('Data')),
        ('time', _('Hora')),
        ('datetime', _('Data e Hora')),
        ('image', _('Imagem')),
        ('gallery', _('Galeria de imagens')),
        ('file', _('Arquivo')),
        ('video', _('Vídeo')),
        ('audio', _('Áudio')),
        ('map', _('Mapa')),
        ('color', _('Cor')),
        ('select', _('Lista de seleção')),
        ('multiselect', _('Lista de seleção múltipla')),
        ('radio', _('Botões de opção')),
        ('checkboxes', _('Lista de checkboxes')),
        ('json', _('Campo JSON')),
        ('code', _('Código fonte')),
        ('relation', _('Relação com outros objetos')),
    )
    
    name = models.CharField(_('Nome'), max_length=100)
    slug = models.SlugField(_('Slug'), max_length=120)
    description = models.TextField(_('Descrição'), blank=True)
    help_text = models.CharField(_('Texto de ajuda'), max_length=255, blank=True)
    field_type = models.CharField(_('Tipo de campo'), max_length=20, choices=FIELD_TYPES)
    default_value = models.TextField(_('Valor padrão'), blank=True)
    placeholder = models.CharField(_('Placeholder'), max_length=255, blank=True)
    is_required = models.BooleanField(_('Campo obrigatório'), default=False)
    min_length = models.IntegerField(_('Comprimento mínimo'), null=True, blank=True)
    max_length = models.IntegerField(_('Comprimento máximo'), null=True, blank=True)
    min_value = models.FloatField(_('Valor mínimo'), null=True, blank=True)
    max_value = models.FloatField(_('Valor máximo'), null=True, blank=True)
    options = models.TextField(_('Opções'), blank=True, 
                           help_text=_('Para campos de seleção, opções separadas por vírgula ou em formato JSON'))
    validation_regex = models.CharField(_('Expressão regular para validação'), max_length=255, blank=True, 
                                     help_text=_('Expressão regular para validação personalizada'))
    allowed_extensions = models.CharField(_('Extensões permitidas'), max_length=255, blank=True, 
                                      help_text=_('Para arquivos e imagens, extensões permitidas separadas por vírgula'))
    max_file_size = models.IntegerField(_('Tamanho máximo de arquivo (KB)'), null=True, blank=True, 
                                     help_text=_('Para arquivos, imagens, vídeos, etc.'))
    group = models.ForeignKey(FieldGroup, on_delete=models.CASCADE, related_name='fields', 
                           verbose_name=_('Grupo de campos'))
    order = models.IntegerField(_('Ordem'), default=0)
    css_classes = models.CharField(_('Classes CSS'), max_length=255, blank=True, 
                                help_text=_('Classes CSS para customizar a aparência do campo'))
    is_searchable = models.BooleanField(_('Pode ser usado em buscas'), default=True)
    is_filterable = models.BooleanField(_('Pode ser usado em filtros'), default=False)
    is_translatable = models.BooleanField(_('Pode ser traduzido'), default=True)
    
    class Meta:
        verbose_name = _('Definição de campo')
        verbose_name_plural = _('Definições de campos')
        ordering = ['group', 'order', 'name']
        unique_together = ('group', 'slug')
    
    def __str__(self):
        return f"{self.group.template.name} - {self.group.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_options_as_list(self):
        """Retorna as opções como uma lista"""
        if not self.options:
            return []
        try:
            # Tenta parser como JSON
            return json.loads(self.options)
        except json.JSONDecodeError:
            # Se não for JSON, assume que é uma lista separada por vírgulas
            return [opt.strip() for opt in self.options.split(',')]
    
    def get_allowed_extensions_as_list(self):
        """Retorna as extensões permitidas como uma lista"""
        if not self.allowed_extensions:
            return []
        return [ext.strip() for ext in self.allowed_extensions.split(',')]


class Page(MPTTModel):
    """
    Modelo principal para páginas do site
    """
    STATUS_CHOICES = (
        ('draft', _('Rascunho')),
        ('review', _('Em revisão')),
        ('scheduled', _('Agendado')),
        ('published', _('Publicado')),
        ('archived', _('Arquivado')),
    )
    
    # Campos básicos
    title = models.CharField(_('Título'), max_length=200)
    slug = models.SlugField(_('Slug'), max_length=250, unique=True)
    content = CKEditor5Field(_('Conteúdo principal'), blank=True)
    summary = models.TextField(_('Resumo'), blank=True)
    
    # Hierarquia e categorização
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                          related_name='children', verbose_name=_('Página pai'))
    categories = models.ManyToManyField(PageCategory, blank=True, related_name='pages', 
                                      verbose_name=_('Categorias'))
    
    # Template e layout
    template = models.ForeignKey(PageTemplate, on_delete=models.CASCADE, 
                               related_name='pages', verbose_name=_('Template'))
    
    # Status e publicação
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='draft')
    is_indexable = models.BooleanField(_('Indexável por motores de busca'), default=True)
    is_searchable = models.BooleanField(_('Aparece nas buscas internas'), default=True)
    is_visible_in_menu = models.BooleanField(_('Visível no menu'), default=True)
    visibility = models.CharField(_('Visibilidade'), max_length=20, 
                               choices=(('public', _('Público')), ('private', _('Privado')), 
                                       ('password', _('Protegido por senha'))),
                               default='public')
    password = models.CharField(_('Senha'), max_length=128, blank=True, 
                             help_text=_('Para páginas protegidas por senha'))
    
    # Datas
    created_at = models.DateTimeField(_('Data de criação'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Última atualização'), auto_now=True)
    published_at = models.DateTimeField(_('Data de publicação'), null=True, blank=True)
    scheduled_at = models.DateTimeField(_('Data agendada'), null=True, blank=True)
    
    # SEO e metadados
    meta_title = models.CharField(_('Título SEO'), max_length=150, blank=True, 
                               help_text=_('Título para SEO. Se vazio, usa o título da página'))
    meta_description = models.TextField(_('Descrição SEO'), blank=True, max_length=300, 
                                     help_text=_('Breve descrição para SEO (máx. 300 caracteres)'))
    meta_keywords = models.CharField(_('Palavras-chave'), max_length=300, blank=True, 
                                  help_text=_('Palavras-chave para SEO, separadas por vírgula'))
    
    # Open Graph
    og_title = models.CharField(_('Título Open Graph'), max_length=150, blank=True, 
                             help_text=_('Título para compartilhamento em redes sociais'))
    og_description = models.TextField(_('Descrição Open Graph'), blank=True, max_length=300, 
                                   help_text=_('Descrição para compartilhamento em redes sociais'))
    og_image = models.ImageField(_('Imagem Open Graph'), upload_to=page_image_path, blank=True, null=True, 
                              help_text=_('Imagem para compartilhamento em redes sociais (1200x630 recomendado)'))
    og_type = models.CharField(_('Tipo Open Graph'), max_length=50, 
                            choices=(('website', 'Website'), ('article', 'Article'), ('blog', 'Blog'), 
                                    ('product', 'Product')),
                            default='website')
    
    # Schema.org
    schema_type = models.CharField(_('Tipo Schema.org'), max_length=50, 
                                choices=(('WebPage', 'WebPage'), ('Article', 'Article'), 
                                        ('BlogPosting', 'BlogPosting'), ('Product', 'Product'), 
                                        ('Event', 'Event'), ('Organization', 'Organization'), 
                                        ('Person', 'Person'), ('LocalBusiness', 'LocalBusiness')), 
                                default='WebPage')
    schema_data = models.TextField(_('Dados Schema.org'), blank=True, 
                                validators=[validate_json], 
                                help_text=_('JSON adicional para Schema.org'))
    
    # URLs e redirecionamentos
    permalink = models.CharField(_('URL permanente'), max_length=255, blank=True, 
                              help_text=_('URL personalizada para esta página. Se vazio, usa o slug'))
    redirect_to = models.CharField(_('Redirecionar para'), max_length=255, blank=True, 
                                help_text=_('Se preenchido, redirecionará para esta URL'))
    redirect_type = models.IntegerField(_('Tipo de redirecionamento'), 
                                     choices=((301, _('Permanente (301)')), (302, _('Temporário (302)'))), 
                                     default=302)
    
    # Rastreamento e cache
    enable_comments = models.BooleanField(_('Habilitar comentários'), default=True)
    enable_analytics = models.BooleanField(_('Habilitar analytics'), default=True)
    cache_ttl = models.IntegerField(_('Tempo de cache (segundos)'), default=3600, 
                                  help_text=_('Tempo para expiração do cache desta página'))

    # Controle e autoria
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, 
                                 related_name='content_pages_created', verbose_name=_('Criado por'))
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, 
                                 related_name='content_pages_updated', verbose_name=_('Atualizado por'))
    published_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='pages_published', verbose_name=_('Publicado por'))
    
    # Ordem na árvore
    order = models.IntegerField(_('Ordem'), default=0)
    
    # Sites
    sites = models.ManyToManyField(Site, related_name='pages', verbose_name=_('Sites'), blank=True)
    
    class Meta:
        verbose_name = _('Página')
        verbose_name_plural = _('Páginas')
        ordering = ['order', 'title']
        permissions = [
            ("publish_page", _("Pode publicar páginas")),
            ("archive_page", _("Pode arquivar páginas")),
            ("review_page", _("Pode revisar páginas")),
        ]
    
    class MPTTMeta:
        order_insertion_by = ['order', 'title']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Gera slug automaticamente se necessário
        if not self.slug:
            self.slug = slugify(self.title)
            
        # Se a página está sendo publicada pela primeira vez
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        
        # Se a página está sendo agendada
        if self.status == 'scheduled' and not self.scheduled_at:
            # Define uma data futura padrão (1 dia depois)
            self.scheduled_at = timezone.now() + timezone.timedelta(days=1)
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Retorna a URL da página"""
        if self.permalink:
            return self.permalink
        
        if self.is_root_node():
            return reverse('pages:page', kwargs={'slug': self.slug})
        else:
            # Constrói a URL com base na hierarquia
            ancestors = self.get_ancestors(include_self=True)
            path = '/'.join([ancestor.slug for ancestor in ancestors])
            return reverse('pages:page_path', kwargs={'path': path})
    
    @property
    def effective_meta_title(self):
        """Retorna o título meta efetivo, usando o título da página se necessário"""
        return self.meta_title or self.title
    
    @property
    def effective_og_title(self):
        """Retorna o título OG efetivo, usando o meta_title ou o título se necessário"""
        return self.og_title or self.meta_title or self.title
    
    @property
    def effective_og_description(self):
        """Retorna a descrição OG efetiva, usando a meta_description se necessário"""
        return self.og_description or self.meta_description or self.summary
    
    def get_schema_json(self):
        """Retorna o JSON Schema.org completo"""
        schema = {
            "@context": "https://schema.org",
            "@type": self.schema_type,
            "name": self.title,
            "description": self.meta_description or self.summary,
            "url": self.get_absolute_url(),
        }
        
        # Adiciona imagem se existir
        if self.og_image:
            schema["image"] = self.og_image.url
        
        # Adiciona dados extras de schema se existirem
        if self.schema_data:
            try:
                extra_schema = json.loads(self.schema_data)
                schema.update(extra_schema)
            except json.JSONDecodeError:
                pass
                
        return schema
    
    def is_published(self):
        """Verifica se a página está publicada"""
        return self.status == 'published' or (
            self.status == 'scheduled' and 
            self.scheduled_at and 
            self.scheduled_at <= timezone.now()
        )
    
    def needs_password(self):
        """Verifica se a página precisa de senha para acesso"""
        return self.visibility == 'password' and bool(self.password)
    
    def check_password(self, password):
        """Verifica se a senha fornecida é válida"""
        return self.password and self.password == password


class PageVersion(models.Model):
    """
    Histórico de versões de páginas para controle de versionamento
    """
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='versions', verbose_name=_('Página'))
    title = models.CharField(_('Título'), max_length=200)
    content = models.TextField(_('Conteúdo'), blank=True)
    summary = models.TextField(_('Resumo'), blank=True)
    version_number = models.IntegerField(_('Número da versão'))
    created_at = models.DateTimeField(_('Data de criação'), auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, 
                                 related_name='page_versions', verbose_name=_('Criado por'))
    comment = models.TextField(_('Comentário da versão'), blank=True)
    
    # Armazena campos personalizados
    custom_fields = models.JSONField(_('Campos personalizados'), blank=True, null=True)
    
    # Status da página nesta versão
    status = models.CharField(_('Status'), max_length=20, choices=Page.STATUS_CHOICES)
    
    # Metadados
    meta_title = models.CharField(_('Título SEO'), max_length=150, blank=True)
    meta_description = models.TextField(_('Descrição SEO'), blank=True, max_length=300)
    meta_keywords = models.CharField(_('Palavras-chave'), max_length=300, blank=True)
    
    class Meta:
        verbose_name = _('Versão de página')
        verbose_name_plural = _('Versões de páginas')
        ordering = ['-version_number']
        unique_together = ('page', 'version_number')
    
    def __str__(self):
        return f"{self.page.title} - {_('Versão')} {self.version_number}"
    
    def restore(self):
        """Restaura esta versão para a página atual"""
        page = self.page
        page.title = self.title
        page.content = self.content
        page.summary = self.summary
        page.meta_title = self.meta_title
        page.meta_description = self.meta_description
        page.meta_keywords = self.meta_keywords
        
        # Restaura os campos personalizados se existirem
        if self.custom_fields:
            PageFieldValue.objects.filter(page=page).delete()
            for field_slug, value in self.custom_fields.items():
                try:
                    field_parts = field_slug.split('.')
                    group_slug = field_parts[0]
                    field_slug = field_parts[1]
                    
                    group = FieldGroup.objects.get(template=page.template, slug=group_slug)
                    field = FieldDefinition.objects.get(group=group, slug=field_slug)
                    
                    PageFieldValue.objects.create(
                        page=page,
                        field=field,
                        value=value
                    )
                except (IndexError, FieldGroup.DoesNotExist, FieldDefinition.DoesNotExist):
                    pass
        
        page.updated_by = self.created_by
        page.save()
        
        return page


class PageFieldValue(models.Model):
    """
    Valores para campos personalizados de páginas
    """
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='field_values', 
                          verbose_name=_('Página'))
    field = models.ForeignKey(FieldDefinition, on_delete=models.CASCADE, related_name='field_values', 
                           verbose_name=_('Campo'))
    value = models.TextField(_('Valor'), blank=True)
    
    # Para campos do tipo arquivo, imagem, etc.
    file = models.FileField(_('Arquivo'), upload_to=page_file_path, blank=True, null=True)
    
    # Para campos que referenciam objetos genericamente (como outras páginas, produtos, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        verbose_name = _('Valor de campo personalizado')
        verbose_name_plural = _('Valores de campos personalizados')
        unique_together = ('page', 'field')
    
    def __str__(self):
        return f"{self.page.title} - {self.field.name}"
    
    def save(self, *args, **kwargs):
        # Validação com base no tipo de campo
        field_type = self.field.field_type
        
        # Validações básicas
        if self.field.is_required and not (self.value or self.file or self.object_id):
            raise ValidationError(_("Este campo é obrigatório"))
        
        # Validações específicas por tipo
        if self.value:
            if field_type in ['text', 'textarea', 'richtext'] and self.field.max_length:
                if len(self.value) > self.field.max_length:
                    raise ValidationError(_("O texto excede o tamanho máximo permitido"))
            
            if field_type in ['integer', 'decimal']:
                try:
                    num_value = float(self.value)
                    if self.field.min_value is not None and num_value < self.field.min_value:
                        raise ValidationError(_("O valor é menor que o mínimo permitido"))
                    if self.field.max_value is not None and num_value > self.field.max_value:
                        raise ValidationError(_("O valor é maior que o máximo permitido"))
                except ValueError:
                    raise ValidationError(_("Valor numérico inválido"))
            
            if field_type == 'email' and '@' not in self.value:
                raise ValidationError(_("E-mail inválido"))
            
            if field_type == 'url' and not (self.value.startswith('http://') or self.value.startswith('https://')):
                raise ValidationError(_("URL inválida"))
            
            if field_type == 'json':
                try:
                    json.loads(self.value)
                except json.JSONDecodeError:
                    raise ValidationError(_("JSON inválido"))
            
            if field_type in ['select', 'radio'] and self.value not in self.field.get_options_as_list():
                raise ValidationError(_("Valor não está entre as opções válidas"))
        
        # Validação de expressão regular
        if self.value and self.field.validation_regex:
            import re
            pattern = re.compile(self.field.validation_regex)
            if not pattern.match(self.value):
                raise ValidationError(_("O valor não corresponde ao padrão de validação"))
                
        # Validação de arquivo
        if self.file and self.field.field_type in ['file', 'image', 'video', 'audio']:
            # Verificar tamanho do arquivo
            if self.field.max_file_size and self.file.size > self.field.max_file_size * 1024:
                raise ValidationError(_("O arquivo excede o tamanho máximo permitido"))
                
            # Verificar extensão do arquivo
            if self.field.allowed_extensions:
                ext = os.path.splitext(self.file.name)[1][1:].lower()
                if ext not in self.field.get_allowed_extensions_as_list():
                    raise ValidationError(_("Tipo de arquivo não permitido"))
        
        super().save(*args, **kwargs)
    
    def get_value_display(self):
        """Retorna o valor formatado para exibição"""
        field_type = self.field.field_type
        
        if field_type in ['file', 'image', 'video', 'audio'] and self.file:
            return self.file.url
        
        if field_type == 'boolean':
            return _('Sim') if self.value.lower() in ['true', '1', 't', 'y', 'yes', 's', 'sim'] else _('Não')
        
        if field_type in ['select', 'radio'] and self.value:
            # Para campos de seleção, retorna o valor legível
            options = self.field.get_options_as_list()
            try:
                # Tenta buscar opções em formato de dicionário {"value": "label"}
                option_dict = {opt['value']: opt['label'] for opt in options if isinstance(opt, dict) and 'value' in opt and 'label' in opt}
                if option_dict and self.value in option_dict:
                    return option_dict[self.value]
            except (TypeError, KeyError):
                pass
                
            # Se não estiver em formato de dicionário, retorna o próprio valor
            return self.value
            
        if field_type == 'relation' and self.content_object:
            return str(self.content_object)
            
        return self.value


class PageRedirect(models.Model):
    """
    Redirecionamentos para URLs antigas ou alternativas de páginas
    """
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='redirects', 
                          verbose_name=_('Página de destino'))
    old_path = models.CharField(_('Caminho antigo'), max_length=255, unique=True,
                             help_text=_('Caminho da URL antiga (ex: /antiga-url/)'))
    redirect_type = models.IntegerField(_('Tipo de redirecionamento'), 
                                     choices=((301, _('Permanente (301)')), (302, _('Temporário (302)'))), 
                                     default=301)
    created_at = models.DateTimeField(_('Data de criação'), auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='redirects_created', verbose_name=_('Criado por'))
    is_active = models.BooleanField(_('Ativo'), default=True)
    access_count = models.PositiveIntegerField(_('Contador de acessos'), default=0)
    last_accessed = models.DateTimeField(_('Último acesso'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Redirecionamento')
        verbose_name_plural = _('Redirecionamentos')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.old_path} → {self.page.title}"
    
    def increment_access(self):
        """Incrementa o contador de acessos e atualiza a data do último acesso"""
        self.access_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed'])


class PageGallery(models.Model):
    """
    Galerias de imagens que podem ser associadas a páginas
    """
    name = models.CharField(_('Nome'), max_length=100)
    slug = models.SlugField(_('Slug'), max_length=120, unique=True)
    description = models.TextField(_('Descrição'), blank=True)
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='galleries', 
                          verbose_name=_('Página'))
    created_at = models.DateTimeField(_('Data de criação'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Última atualização'), auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, 
                                 related_name='galleries_created', verbose_name=_('Criado por'))
    
    class Meta:
        verbose_name = _('Galeria')
        verbose_name_plural = _('Galerias')
        ordering = ['name']
        
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PageImage(models.Model):
    """
    Imagens para galerias de páginas
    """
    gallery = models.ForeignKey(PageGallery, on_delete=models.CASCADE, related_name='images', 
                             verbose_name=_('Galeria'))
    image = models.ImageField(_('Imagem'), upload_to=page_image_path)
    title = models.CharField(_('Título'), max_length=200, blank=True)
    alt_text = models.CharField(_('Texto alternativo'), max_length=255, blank=True)
    description = models.TextField(_('Descrição'), blank=True)
    order = models.IntegerField(_('Ordem'), default=0)
    created_at = models.DateTimeField(_('Data de adição'), auto_now_add=True)
    
    # Metadados da imagem
    width = models.IntegerField(_('Largura'), blank=True, null=True)
    height = models.IntegerField(_('Altura'), blank=True, null=True)
    file_size = models.IntegerField(_('Tamanho do arquivo (KB)'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Imagem')
        verbose_name_plural = _('Imagens')
        ordering = ['gallery', 'order', 'title']
        
    def __str__(self):
        return self.title or self.alt_text or f"{_('Imagem')} {self.id}"
    
    def save(self, *args, **kwargs):
        # Preenche os metadados da imagem
        if self.image and not (self.width and self.height):
            from PIL import Image
            img = Image.open(self.image)
            self.width, self.height = img.size
            
            # Calcular tamanho do arquivo
            if self.image.size:
                self.file_size = self.image.size // 1024  # Conversão para KB
                
        super().save(*args, **kwargs)


class PageComment(models.Model):
    """
    Comentários de usuários em páginas
    """
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='comments', 
                          verbose_name=_('Página'))
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                            related_name='replies', verbose_name=_('Comentário pai'))
    author_name = models.CharField(_('Nome do autor'), max_length=100)
    author_email = models.EmailField(_('E-mail do autor'))
    author_url = models.URLField(_('Website do autor'), blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                          related_name='page_comments', verbose_name=_('Usuário'))
    comment = models.TextField(_('Comentário'))
    created_at = models.DateTimeField(_('Data de criação'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Última atualização'), auto_now=True)
    is_approved = models.BooleanField(_('Aprovado'), default=False)
    ip_address = models.GenericIPAddressField(_('Endereço IP'), blank=True, null=True)
    user_agent = models.CharField(_('User Agent'), max_length=255, blank=True)
    
    # Metadados do comentário
    likes = models.PositiveIntegerField(_('Curtidas'), default=0)
    dislikes = models.PositiveIntegerField(_('Não curtidas'), default=0)
    is_pinned = models.BooleanField(_('Destacado'), default=False)
    
    class Meta:
        verbose_name = _('Comentário')
        verbose_name_plural = _('Comentários')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.author_name}: {self.comment[:50]}"
    
    def approve(self):
        """Aprova o comentário"""
        self.is_approved = True
        self.save(update_fields=['is_approved'])
        
    def get_approval_link(self):
        """Retorna o link para aprovar o comentário"""
        from django.urls import reverse
        return reverse('admin:pages_pagecomment_approve', args=[self.id])
    
    def get_absolute_url(self):
        """Retorna a URL para o comentário na página"""
        return f"{self.page.get_absolute_url()}#comment-{self.id}"


class PageMeta(models.Model):
    """
    Metadados adicionais para páginas (dados extras não presentes no modelo principal)
    """
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='meta_items', 
                          verbose_name=_('Página'))
    key = models.CharField(_('Chave'), max_length=100)
    value = models.TextField(_('Valor'), blank=True)
    
    class Meta:
        verbose_name = _('Metadado')
        verbose_name_plural = _('Metadados')
        unique_together = ('page', 'key')
        
    def __str__(self):
        return f"{self.page.title} - {self.key}"


class PageRevisionRequest(models.Model):
    """
    Solicitações de revisão para páginas
    """
    STATUS_CHOICES = (
        ('pending', _('Pendente')),
        ('in_progress', _('Em análise')),
        ('approved', _('Aprovado')),
        ('rejected', _('Rejeitado')),
    )
    
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='revision_requests', 
                          verbose_name=_('Página'))
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='revision_requests_created', 
                                   verbose_name=_('Solicitado por'))
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='revisions_assigned', verbose_name=_('Revisor'))
    comment = models.TextField(_('Comentário'), blank=True)
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(_('Data da solicitação'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Última atualização'), auto_now=True)
    completed_at = models.DateTimeField(_('Data de conclusão'), null=True, blank=True)
    reviewer_comment = models.TextField(_('Comentário do revisor'), blank=True)
    
    # Versão específica para revisão (se aplicável)
    version = models.ForeignKey(PageVersion, on_delete=models.SET_NULL, null=True, blank=True, 
                             related_name='revision_requests', verbose_name=_('Versão'))
    
    class Meta:
        verbose_name = _('Solicitação de revisão')
        verbose_name_plural = _('Solicitações de revisão')
        ordering = ['-requested_at']
        
    def __str__(self):
        return f"{self.page.title} - {self.get_status_display()}"
    
    def approve(self, reviewer=None, comment=''):
        """Aprova a solicitação de revisão"""
        self.status = 'approved'
        self.reviewer = reviewer or self.reviewer
        self.reviewer_comment = comment
        self.completed_at = timezone.now()
        self.save()
        
        # Se for uma versão específica, marca a página como publicada
        if self.version:
            self.page.status = 'published'
            self.page.published_at = timezone.now()
            self.page.published_by = self.reviewer
            self.page.save()
        
    def reject(self, reviewer=None, comment=''):
        """Rejeita a solicitação de revisão"""
        self.status = 'rejected'
        self.reviewer = reviewer or self.reviewer
        self.reviewer_comment = comment
        self.completed_at = timezone.now()
        self.save()


class PageNotification(models.Model):
    """
    Notificações sobre ações em páginas
    """
    NOTIFICATION_TYPES = (
        ('page_created', _('Página criada')),
        ('page_updated', _('Página atualizada')),
        ('page_published', _('Página publicada')),
        ('page_archived', _('Página arquivada')),
        ('page_deleted', _('Página excluída')),
        ('revision_requested', _('Revisão solicitada')),
        ('revision_approved', _('Revisão aprovada')),
        ('revision_rejected', _('Revisão rejeitada')),
        ('comment_added', _('Comentário adicionado')),
    )
    
    notification_type = models.CharField(_('Tipo de notificação'), max_length=30, choices=NOTIFICATION_TYPES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='page_notifications', 
                          verbose_name=_('Usuário'))
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='notifications', 
                          verbose_name=_('Página'))
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                           related_name='page_actions', verbose_name=_('Ator'))
    message = models.TextField(_('Mensagem'))
    created_at = models.DateTimeField(_('Data de criação'), auto_now_add=True)
    is_read = models.BooleanField(_('Lida'), default=False)
    read_at = models.DateTimeField(_('Data de leitura'), null=True, blank=True)
    
    # Informações adicionais em formato JSON
    extra_data = models.JSONField(_('Dados adicionais'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Notificação')
        verbose_name_plural = _('Notificações')
        ordering = ['-created_at']
        
    def __str__(self):
        return self.message
    
    def mark_as_read(self):
        """Marca a notificação como lida"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])
        
    @classmethod
    def create_notification(cls, notification_type, page, user, actor=None, extra_data=None):
        """
        Cria uma nova notificação
        
        Args:
            notification_type: Tipo de notificação
            page: Página relacionada
            user: Usuário que receberá a notificação
            actor: Usuário que realizou a ação
            extra_data: Dados adicionais em formato dict
        """
        # Monta a mensagem com base no tipo de notificação
        messages = {
            'page_created': _('Página "{title}" foi criada por {actor}'),
            'page_updated': _('Página "{title}" foi atualizada por {actor}'),
            'page_published': _('Página "{title}" foi publicada por {actor}'),
            'page_archived': _('Página "{title}" foi arquivada por {actor}'),
            'page_deleted': _('Página "{title}" foi excluída por {actor}'),
            'revision_requested': _('Revisão solicitada para a página "{title}" por {actor}'),
            'revision_approved': _('Revisão da página "{title}" foi aprovada por {actor}'),
            'revision_rejected': _('Revisão da página "{title}" foi rejeitada por {actor}'),
            'comment_added': _('Novo comentário na página "{title}" por {actor}'),
        }
        
        actor_name = actor.get_full_name() or actor.username if actor else _('Sistema')
        message = messages.get(notification_type, '').format(title=page.title, actor=actor_name)
        
        notification = cls(
            notification_type=notification_type,
            user=user,
            page=page,
            actor=actor,
            message=message,
            extra_data=extra_data
        )
        notification.save()
        
        return notification 
    
    