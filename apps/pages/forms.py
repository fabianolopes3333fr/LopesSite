# your_cms_app/pages/forms.py

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from mptt.forms import TreeNodeChoiceField
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import (
    Page, PageCategory, PageTemplate, FieldGroup, FieldDefinition, 
    PageFieldValue, PageComment, PageGallery, PageRevisionRequest
)


class PageBaseForm(forms.ModelForm):
    """
    Formulário base para páginas, usado para criar e editar páginas no frontend
    """
    parent = TreeNodeChoiceField(
        queryset=Page.objects.all(),
        required=False,
        label=_('Página pai'),
        help_text=_('Selecione a página pai para esta página (opcional)'),
        empty_label=_('Nenhum (página raiz)')
    )
    
    content = forms.CharField(
        widget=CKEditor5Widget(),
        required=False,
        label=_('Conteúdo')
    )
    
    class Meta:
        model = Page
        fields = [
            'title', 'slug', 'parent', 'summary', 'content', 'categories',
            'template', 'status', 'visibility', 'password',
            'meta_title', 'meta_description', 'meta_keywords',
            'og_title', 'og_description', 'og_image', 'og_type',
            'schema_type', 'schema_data', 'permalink',
            'is_indexable', 'is_searchable', 'is_visible_in_menu',
            'enable_comments', 'enable_analytics'
        ]
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 3}),
            'meta_description': forms.Textarea(attrs={'rows': 2}),
            'og_description': forms.Textarea(attrs={'rows': 2}),
            'schema_data': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.custom_fields = []
        
        super().__init__(*args, **kwargs)
        
        # Configura as escolhas para o campo parent
        if self.instance.pk:
            # Exclui esta página e seus descendentes das escolhas
            self.fields['parent'].queryset = Page.objects.exclude(
                pk__in=self.instance.get_descendants(include_self=True).values_list('pk', flat=True)
            )
            
            # Carrega os campos personalizados
            self.load_custom_fields()
        
        # Configura o campo de status com base nas permissões do usuário
        if self.user:
            if not self.user.has_perm('pages.publish_page'):
                # Limita as opções de status para usuários sem permissão de publicação
                status_choices = [
                    ('draft', _('Rascunho')),
                    ('review', _('Em revisão'))
                ]
                self.fields['status'].choices = status_choices
    
    def load_custom_fields(self):
        """
        Carrega os campos personalizados com base no template da página
        """
        if not self.instance.pk or not self.instance.template:
            return
            
        # Carrega todos os grupos de campos para o template
        field_groups = FieldGroup.objects.filter(
            template=self.instance.template
        ).order_by('order').prefetch_related('fields')
        
        # Dicionário para armazenar valores existentes
        existing_values = {}
        for field_value in PageFieldValue.objects.filter(page=self.instance).select_related('field'):
            existing_values[field_value.field.id] = field_value
        
        # Para cada grupo, cria campos para cada definição de campo
        for group in field_groups:
            for field_def in group.fields.all().order_by('order'):
                field_key = f'custom_{field_def.id}'
                
                # Valor padrão para o campo
                initial_value = None
                
                # Se já existe um valor para este campo, use-o
                if field_def.id in existing_values:
                    field_value = existing_values[field_def.id]
                    if field_def.field_type in ['file', 'image', 'video', 'audio'] and field_value.file:
                        initial_value = field_value.file
                    else:
                        initial_value = field_value.value
                else:
                    # Caso contrário, use o valor padrão da definição do campo
                    initial_value = field_def.default_value
                
                # Cria o campo no formulário com base no tipo
                field_widget = self.get_field_widget(field_def)
                field_kwargs = {
                    'label': field_def.name,
                    'help_text': field_def.help_text,
                    'required': field_def.is_required,
                    'initial': initial_value,
                    'widget': field_widget
                }
                
                # Adiciona validadores específicos para cada tipo de campo
                if field_def.field_type in ['integer', 'decimal']:
                    if field_def.min_value is not None:
                        field_kwargs['min_value'] = field_def.min_value
                    if field_def.max_value is not None:
                        field_kwargs['max_value'] = field_def.max_value
                
                if field_def.field_type in ['text', 'textarea', 'richtext', 'email', 'url']:
                    if field_def.min_length is not None:
                        field_kwargs['min_length'] = field_def.min_length
                    if field_def.max_length is not None:
                        field_kwargs['max_length'] = field_def.max_length
                
                # Cria um tipo de campo diferente para cada field_type
                if field_def.field_type == 'text':
                    self.fields[field_key] = forms.CharField(**field_kwargs)
                elif field_def.field_type == 'textarea':
                    self.fields[field_key] = forms.CharField(**field_kwargs)
                elif field_def.field_type == 'richtext':
                    self.fields[field_key] = forms.CharField(**field_kwargs)
                elif field_def.field_type == 'email':
                    self.fields[field_key] = forms.EmailField(**field_kwargs)
                elif field_def.field_type == 'url':
                    self.fields[field_key] = forms.URLField(**field_kwargs)
                elif field_def.field_type == 'integer':
                    self.fields[field_key] = forms.IntegerField(**field_kwargs)
                elif field_def.field_type == 'decimal':
                    self.fields[field_key] = forms.DecimalField(**field_kwargs)
                elif field_def.field_type == 'boolean':
                    self.fields[field_key] = forms.BooleanField(**field_kwargs)
                elif field_def.field_type == 'date':
                    self.fields[field_key] = forms.DateField(**field_kwargs)
                elif field_def.field_type == 'time':
                    self.fields[field_key] = forms.TimeField(**field_kwargs)
                elif field_def.field_type == 'datetime':
                    self.fields[field_key] = forms.DateTimeField(**field_kwargs)
                elif field_def.field_type == 'select':
                    choices = self.get_field_choices(field_def)
                    self.fields[field_key] = forms.ChoiceField(choices=choices, **field_kwargs)
                elif field_def.field_type == 'multiselect':
                    choices = self.get_field_choices(field_def)
                    self.fields[field_key] = forms.MultipleChoiceField(choices=choices, **field_kwargs)
                elif field_def.field_type == 'radio':
                    choices = self.get_field_choices(field_def)
                    self.fields[field_key] = forms.ChoiceField(choices=choices, widget=forms.RadioSelect, **field_kwargs)
                elif field_def.field_type == 'checkboxes':
                    choices = self.get_field_choices(field_def)
                    self.fields[field_key] = forms.MultipleChoiceField(
                        choices=choices, 
                        widget=forms.CheckboxSelectMultiple, 
                        **field_kwargs
                    )
                elif field_def.field_type == 'image':
                    self.fields[field_key] = forms.ImageField(**field_kwargs)
                elif field_def.field_type == 'file':
                    self.fields[field_key] = forms.FileField(**field_kwargs)
                elif field_def.field_type == 'video':
                    self.fields[field_key] = forms.FileField(**field_kwargs)
                elif field_def.field_type == 'audio':
                    self.fields[field_key] = forms.FileField(**field_kwargs)
                elif field_def.field_type == 'color':
                    self.fields[field_key] = forms.CharField(**field_kwargs)
                elif field_def.field_type == 'json':
                    self.fields[field_key] = forms.CharField(**field_kwargs)
                elif field_def.field_type == 'code':
                    self.fields[field_key] = forms.CharField(**field_kwargs)
                elif field_def.field_type == 'map':
                    self.fields[field_key] = forms.CharField(**field_kwargs)
                elif field_def.field_type == 'gallery':
                    # Para galerias, usaremos um campo de texto que armazenará IDs de imagens
                    self.fields[field_key] = forms.CharField(**field_kwargs)
                elif field_def.field_type == 'relation':
                    # Para campos de relação, usaremos um campo de escolha
                    self.fields[field_key] = forms.ChoiceField(**field_kwargs)
                
                # Registra o campo customizado
                self.custom_fields.append({
                    'key': field_key,
                    'field_def': field_def,
                    'group': group
                })
    
    def get_field_widget(self, field_def):
        """
        Retorna o widget apropriado para um tipo de campo
        """
        attrs = {}
        
        # Adiciona placeholder se definido
        if field_def.placeholder:
            attrs['placeholder'] = field_def.placeholder
            
        # Adiciona classes CSS
        if field_def.css_classes:
            attrs['class'] = field_def.css_classes
            
        # Define o widget com base no tipo de campo
        if field_def.field_type == 'text':
            return forms.TextInput(attrs=attrs)
        elif field_def.field_type == 'textarea':
            attrs['rows'] = 4
            return forms.Textarea(attrs=attrs)
        elif field_def.field_type == 'richtext':
            return CKEditor5Widget(config_name='default', attrs=attrs)
        elif field_def.field_type == 'email':
            return forms.EmailInput(attrs=attrs)
        elif field_def.field_type == 'url':
            return forms.URLInput(attrs=attrs)
        elif field_def.field_type == 'integer':
            return forms.NumberInput(attrs=attrs)
        elif field_def.field_type == 'decimal':
            return forms.NumberInput(attrs={**attrs, 'step': '0.01'})
        elif field_def.field_type == 'date':
            return forms.DateInput(attrs={**attrs, 'type': 'date'})
        elif field_def.field_type == 'time':
            return forms.TimeInput(attrs={**attrs, 'type': 'time'})
        elif field_def.field_type == 'datetime':
            return forms.DateTimeInput(attrs={**attrs, 'type': 'datetime-local'})
        elif field_def.field_type == 'color':
            return forms.TextInput(attrs={**attrs, 'type': 'color'})
        elif field_def.field_type == 'json':
            attrs['rows'] = 6
            return forms.Textarea(attrs=attrs)
        elif field_def.field_type == 'code':
            attrs['rows'] = 10
            return forms.Textarea(attrs=attrs)
        elif field_def.field_type == 'map':
            # Widget personalizado para mapas seria ideal
            return forms.TextInput(attrs=attrs)
            
        # Para outros tipos, retorna um TextInput padrão
        return forms.TextInput(attrs=attrs)
    
    def get_field_choices(self, field_def):
        """
        Retorna as opções de escolha para campos select, radio, etc.
        """
        choices = []
        
        # Se o campo é obrigatório, não adiciona opção vazia
        if not field_def.is_required:
            choices.append(('', '---------'))
            
        # Obtém as opções do campo
        options = field_def.get_options_as_list()
        
        # Verifica se as opções estão no formato de dicionário
        if options and isinstance(options[0], dict) and 'value' in options[0] and 'label' in options[0]:
            # Formato: [{'value': 'valor1', 'label': 'Label 1'}, ...]
            for option in options:
                choices.append((option['value'], option['label']))
        else:
            # Formato simples: ['Opção 1', 'Opção 2', ...]
            for option in options:
                choices.append((option, option))
                
        return choices
    
    def save(self, commit=True):
        """
        Salva a página e seus campos personalizados
        """
        # Verifica se é uma publicação e o usuário tem permissão
        is_publishing = (
            self.cleaned_data.get('status') == 'published' and 
            self.instance.status != 'published'
        )
        
        if is_publishing and self.user and not self.user.has_perm('pages.publish_page'):
            # Se o usuário não tem permissão para publicar, muda para revisão
            self.cleaned_data['status'] = 'review'
        
        # Registra a data de publicação se necessário
        if self.cleaned_data.get('status') == 'published' and not self.instance.published_at:
            self.instance.published_at = timezone.now()
            if self.user:
                self.instance.published_by = self.user
        
        # Registra o usuário que criou ou atualizou a página
        if not self.instance.pk and self.user:
            self.instance.created_by = self.user
        if self.user:
            self.instance.updated_by = self.user
            
        # Salva a página
        page = super().save(commit=commit)
        
        # Salva os campos personalizados
        if commit and hasattr(self, 'custom_fields'):
            self.save_custom_fields(page)
            
        return page
    
    def save_custom_fields(self, page):
        """
        Salva os valores dos campos personalizados
        """
        for custom_field in self.custom_fields:
            field_key = custom_field['key']
            field_def = custom_field['field_def']
            
            if field_key in self.cleaned_data:
                field_value = self.cleaned_data[field_key]
                
                # Procura por um valor existente ou cria um novo
                try:
                    field_value_obj = PageFieldValue.objects.get(page=page, field=field_def)
                except PageFieldValue.DoesNotExist:
                    field_value_obj = PageFieldValue(page=page, field=field_def)
                
                # Salva o valor dependendo do tipo de campo
                if field_def.field_type in ['file', 'image', 'video', 'audio'] and field_value:
                    field_value_obj.file = field_value
                    field_value_obj.value = ""
                elif field_def.field_type in ['select', 'radio', 'checkboxes', 'multiselect']:
                    # Para campos de múltipla escolha, converte para string JSON
                    if isinstance(field_value, list):
                        import json
                        field_value_obj.value = json.dumps(field_value)
                    else:
                        field_value_obj.value = field_value
                else:
                    # Para outros tipos, salva como string
                    field_value_obj.value = str(field_value) if field_value is not None else ""
                
                field_value_obj.save()


class PagePublishForm(forms.Form):
    """
    Formulário para publicação de páginas
    """
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label=_('Comentário de publicação'),
        required=False,
        help_text=_('Opcional: adicione um comentário sobre esta publicação')
    )


class PageReviewRequestForm(forms.Form):
    """
    Formulário para solicitação de revisão de páginas
    """
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label=_('Comentário para o revisor'),
        required=True,
        help_text=_('Explique as alterações realizadas e por que a página está pronta para revisão')
    )
    
    def save(self, page, user):
        """
        Cria uma solicitação de revisão para a página
        """
        # Muda o status da página para 'em revisão'
        page.status = 'review'
        page.save(update_fields=['status'])
        
        # Cria a solicitação de revisão
        request = PageRevisionRequest.objects.create(
            page=page,
            requested_by=user,
            comment=self.cleaned_data['comment'],
            status='pending'
        )
        
        # Notifica os revisores
        from django.contrib.auth.models import User, Permission
        from django.contrib.contenttypes.models import ContentType
        from .models import PageNotification
        
        content_type = ContentType.objects.get_for_model(Page)
        publish_permission = Permission.objects.get(
            content_type=content_type, 
            codename='publish_page'
        )
        
        reviewers = User.objects.filter(
            is_staff=True,
            is_active=True,
            user_permissions=publish_permission
        ).exclude(id=user.id)
        
        for reviewer in reviewers:
            PageNotification.create_notification(
                'revision_requested',
                page,
                reviewer,
                user,
                {'review_id': request.id}
            )
            
        return request


class PageCommentForm(forms.ModelForm):
    """
    Formulário para comentários em páginas
    """
    class Meta:
        model = PageComment
        fields = ['author_name', 'author_email', 'author_url', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.page = kwargs.pop('page', None)
        self.user = kwargs.pop('user', None)
        self.parent = kwargs.pop('parent', None)
        self.request = kwargs.pop('request', None)
        
        super().__init__(*args, **kwargs)
        
        # Se o usuário estiver autenticado, preenche automaticamente
        if self.user and self.user.is_authenticated:
            self.fields['author_name'].initial = self.user.get_full_name() or self.user.username
            self.fields['author_email'].initial = self.user.email
            
            # Torna os campos de autor somente leitura para usuários autenticados
            self.fields['author_name'].widget.attrs['readonly'] = True
            self.fields['author_email'].widget.attrs['readonly'] = True
    
    def save(self, commit=True):
        """
        Salva o comentário com informações adicionais
        """
        comment = super().save(commit=False)
        
        # Associa à página, ao usuário e ao comentário pai
        comment.page = self.page
        if self.user and self.user.is_authenticated:
            comment.user = self.user
        if self.parent:
            comment.parent = self.parent
            
        # Registra informações do request
        if self.request:
            comment.ip_address = self.request.META.get('REMOTE_ADDR', '')
            comment.user_agent = self.request.META.get('HTTP_USER_AGENT', '')
            
        # Define se o comentário já será aprovado automaticamente
        if self.user and self.user.is_staff:
            comment.is_approved = True
            
        if commit:
            comment.save()
            
            # Notifica o autor da página
            if self.page.created_by and self.page.created_by != self.user:
                from .models import PageNotification
                PageNotification.create_notification(
                    'comment_added',
                    self.page,
                    self.page.created_by,
                    self.user or None,
                    {'comment_id': comment.id}
                )
            
        return comment


class PageSearchForm(forms.Form):
    """
    Formulário para busca de páginas
    """
    q = forms.CharField(
        required=False,
        label=_('Buscar'),
        widget=forms.TextInput(attrs={'placeholder': _('Digite sua busca...')})
    )
    category = forms.ModelChoiceField(
        queryset=PageCategory.objects.filter(is_active=True),
        required=False,
        label=_('Categoria'),
        empty_label=_('Todas as categorias')
    )
    date_from = forms.DateField(
        required=False,
        label=_('Data inicial'),
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        label=_('Data final'),
        widget=forms.DateInput(attrs={'type': 'date'})
    )


class GalleryForm(forms.ModelForm):
    """
    Formulário para criar e editar galerias
    """
    class Meta:
        model = PageGallery
        fields = ['name', 'slug', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.page = kwargs.pop('page', None)
        self.user = kwargs.pop('user', None)
        
        super().__init__(*args, **kwargs)
        
        # Pré-popula o slug se não for uma edição
        if not self.instance.pk and 'name' in self.initial:
            from django.utils.text import slugify
            self.initial['slug'] = slugify(self.initial['name'])
    
    def save(self, commit=True):
        """
        Salva a galeria com informações adicionais
        """
        gallery = super().save(commit=False)
        
        # Associa à página e ao usuário
        if self.page:
            gallery.page = self.page
        if self.user:
            gallery.created_by = self.user
            
        if commit:
            gallery.save()
            
        return gallery