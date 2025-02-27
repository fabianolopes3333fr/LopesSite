# your_cms_app/pages/admin.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils import timezone
from django.db import models
from django.forms import TextInput, Textarea
from django import forms
from django.contrib.admin.widgets import AdminFileWidget
from django.db.models import Count
from mptt.admin import MPTTModelAdmin, DraggableMPTTAdmin
import csv
from django.http import HttpResponse
from django.template.response import TemplateResponse
from .forms import PageForm
from .models import (
    PageApproval, PageCategory, PageStatusHistory, PageTemplate, FieldGroup, FieldDefinition, Page, PageVersion,
    PageFieldValue, PageRedirect, PageGallery, PageImage, PageComment,
    PageMeta, PageRevisionRequest, PageNotification
)

class PageStatusHistoryInline(admin.TabularInline):
    model = PageStatusHistory
    extra = 0
    readonly_fields = ('changed_at', 'changed_by', 'old_status', 'new_status')
    can_delete = False

class PageApprovalInline(admin.TabularInline):
    model = PageApproval
    extra = 0
    readonly_fields = ('requested_by', 'requested_at', 'approved_by', 'approved_at')
    can_delete = False


class FieldGroupInline(admin.TabularInline):
    """Inline para grupos de campos em templates de página"""
    model = FieldGroup
    extra = 1
    prepopulated_fields = {'slug': ('name',)}


class FieldDefinitionInline(admin.TabularInline):
    """Inline para definições de campos em grupos de campos"""
    model = FieldDefinition
    extra = 1
    prepopulated_fields = {'slug': ('name',)}
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 3, 'cols': 40})},
    }


class PageCategoryAdmin(DraggableMPTTAdmin):
    """Administração de categorias de páginas"""
    list_display = ('tree_actions', 'indented_title', 'slug', 'icon', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    mptt_level_indent = 20
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('name', 'slug', 'description', 'parent')
        }),
        (_('Aparência'), {
            'fields': ('icon', 'color', 'is_active', 'order')
        }),
    )


class PageTemplateAdmin(admin.ModelAdmin):
    """Administração de templates de página"""
    list_display = ('name', 'slug', 'layout', 'is_active', 'field_groups_count', 'created_at')
    list_filter = ('layout', 'is_active')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [FieldGroupInline]
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('name', 'slug', 'description', 'template_file')
        }),
        (_('Configurações'), {
            'fields': ('layout', 'is_active', 'preview_image')
        }),
    )
    
    def field_groups_count(self, obj):
        """Retorna o número de grupos de campos no template"""
        return obj.field_groups.count()
    field_groups_count.short_description = _('Grupos de campos')


class FieldGroupAdmin(admin.ModelAdmin):
    """Administração de grupos de campos"""
    list_display = ('name', 'slug', 'template', 'order', 'is_collapsible', 'is_collapsed', 'fields_count')
    list_filter = ('template', 'is_collapsible', 'is_collapsed')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [FieldDefinitionInline]
    
    def fields_count(self, obj):
        """Retorna o número de campos no grupo"""
        return obj.fields.count()
    fields_count.short_description = _('Campos')


class FieldDefinitionAdmin(admin.ModelAdmin):
    """Administração de definições de campos"""
    list_display = ('name', 'slug', 'group', 'field_type', 'is_required', 'order', 'is_searchable')
    list_filter = ('field_type', 'is_required', 'is_searchable', 'is_filterable', 'group__template')
    search_fields = ('name', 'slug', 'description', 'help_text')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('name', 'slug', 'description', 'help_text', 'group', 'order')
        }),
        (_('Configurações de Campo'), {
            'fields': ('field_type', 'is_required', 'placeholder', 'default_value')
        }),
        (_('Validação'), {
            'fields': ('min_length', 'max_length', 'min_value', 'max_value', 
                      'validation_regex', 'allowed_extensions', 'max_file_size')
        }),
        (_('Opções'), {
            'fields': ('options',)
        }),
        (_('Exibição e Pesquisa'), {
            'fields': ('css_classes', 'is_searchable', 'is_filterable', 'is_translatable')
        }),
    )


class PageFieldValueInline(admin.StackedInline):
    """Inline para valores de campos personalizados em páginas"""
    model = PageFieldValue
    extra = 0
    
    def get_fields(self, request, obj=None):
        """Retorna os campos dinâmicos com base no template da página"""
        if obj is None:
            return ['field', 'value', 'file']
            
        # Obtém os campos agrupados por seu grupo
        field_groups = {}
        for field_value in obj.field_values.select_related('field__group').all():
            group_name = field_value.field.group.name
            if group_name not in field_groups:
                field_groups[group_name] = []
            field_groups[group_name].append(field_value.field.id)
            
        # Define os campos com base nos grupos existentes
        fields = []
        for group_name, field_ids in field_groups.items():
            fields.append(group_name)
            fields.extend(['field', 'value', 'file'])
            
        return fields
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtra os campos disponíveis com base no template da página"""
        if db_field.name == "field":
            if request is not None and '_original_page' in request.POST:
                try:
                    page_id = int(request.POST['_original_page'])
                    page = Page.objects.get(id=page_id)
                    kwargs["queryset"] = FieldDefinition.objects.filter(
                        group__template=page.template
                    ).order_by('group__order', 'order')
                except (ValueError, Page.DoesNotExist):
                    # Fallback para todos os campos se não conseguirmos obter a página
                    kwargs["queryset"] = FieldDefinition.objects.all().order_by('group__order', 'order')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class PageImageInline(admin.TabularInline):
    """Inline para imagens em galerias de páginas"""
    model = PageImage
    extra = 3
    fields = ('image', 'title', 'alt_text', 'order')


class PageGalleryInline(admin.TabularInline):
    """Inline para galerias em páginas"""
    model = PageGallery
    extra = 1
    prepopulated_fields = {'slug': ('name',)}


class PageRedirectInline(admin.TabularInline):
    """Inline para redirecionamentos em páginas"""
    model = PageRedirect
    extra = 1
    fields = ('old_path', 'redirect_type', 'is_active')


class PageMetaInline(admin.TabularInline):
    """Inline para metadados adicionais em páginas"""
    model = PageMeta
    extra = 1


class PageVersionInline(admin.TabularInline):
    """Inline para versões de páginas"""
    model = PageVersion
    extra = 0
    fields = ('version_number', 'status', 'created_at', 'created_by', 'comment')
    readonly_fields = ('version_number', 'status', 'created_at', 'created_by', 'comment')
    can_delete = False
    max_num = 0
    
    def has_add_permission(self, request, obj=None):
        return False


class PageCommentInline(admin.TabularInline):
    """Inline para comentários em páginas"""
    model = PageComment
    extra = 0
    fields = ('author_name', 'author_email', 'comment', 'is_approved', 'created_at')
    readonly_fields = ('author_name', 'author_email', 'created_at')


class PageRevisionRequestInline(admin.TabularInline):
    """Inline para solicitações de revisão em páginas"""
    model = PageRevisionRequest
    extra = 0
    fields = ('requested_by', 'reviewer', 'status', 'requested_at', 'completed_at')
    readonly_fields = ('requested_by', 'reviewer', 'requested_at', 'completed_at')
    can_delete = False
    max_num = 0
    
    def has_add_permission(self, request, obj=None):
        return False





class PageAdmin(DraggableMPTTAdmin):
    """Administração de páginas"""
    form = PageForm
    list_display = ('tree_actions', 'indented_title', 'status', 'template', 'created_at', 'updated_at', 'view_on_site', 'is_published')
    list_filter = ('status', 'template', 'visibility', 'is_indexable', 'is_visible_in_menu', 'categories')
    search_fields = ('title', 'slug', 'meta_title', 'meta_description', 'meta_keywords', 'content')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    actions = ['publish_selected', 'unpublish_selected', 'archive_selected', 'create_new_version']
    save_on_top = True
    mptt_level_indent = 20
    
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('title', 'slug', 'parent', 'summary', 'content')
        }),
        (_('Categorização e Layout'), {
            'fields': ('categories', 'template', 'order')
        }),
        (_('Publicação'), {
            'fields': ('status', 'published_at', 'scheduled_at')
        }),
        (_('Visibilidade'), {
            'fields': ('visibility', 'password', 'is_indexable', 'is_searchable', 'is_visible_in_menu')
        }),
        (_('SEO'), {
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
        (_('Open Graph'), {
            'classes': ('collapse',),
            'fields': ('og_title', 'og_description', 'og_image', 'og_type')
        }),
        (_('Schema.org'), {
            'classes': ('collapse',),
            'fields': ('schema_type', 'schema_data')
        }),
        (_('URLs e Redirecionamentos'), {
            'classes': ('collapse',),
            'fields': ('permalink', 'redirect_to', 'redirect_type')
        }),
        (_('Configurações Avançadas'), {
            'classes': ('collapse',),
            'fields': ('enable_comments', 'enable_analytics', 'cache_ttl', 'sites')
        }),
    )
    
    inlines = [
        PageFieldValueInline,
        PageGalleryInline,
        PageRedirectInline,
        PageMetaInline,
        PageVersionInline,
        PageCommentInline,
        PageRevisionRequestInline,
        PageStatusHistoryInline,
        PageApprovalInline,
    ]
    
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by', 'published_by', 'view_on_site')
    
    class Media:
        js = ('js/seo_preview.js',)  # Arquivo JS para preview em tempo real
    
    def view_on_site(self, obj):
        """Adiciona botão para visualizar a página no site"""
        if obj.pk:
            return format_html(
                '<a href="{}" class="button" target="_blank">{}</a>',
                obj.get_absolute_url(),
                _('Visualizar')
            )
        return ""
    view_on_site.short_description = _('Visualizar no site')
    
    def save_model(self, request, obj, form, change):
        """Salva o modelo com informações adicionais"""
        
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        if not is_new:
            obj.create_version(request.user, _("Automatic version on save"))
            obj.save()
        # Registra o usuário que criou/atualizou a página
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Se o status mudou para 'published'
        if 'status' in form.changed_data and obj.status == 'published':
            obj.published_by = request.user
            obj.published_at = timezone.now()
            
        super().save_model(request, obj, form, change)
        
        # Cria uma nova versão após salvar se houver mudanças
        if form.changed_data:
            version_number = 1
            last_version = PageVersion.objects.filter(page=obj).order_by('-version_number').first()
            if last_version:
                version_number = last_version.version_number + 1
            
            # Coleta os valores dos campos personalizados
            custom_fields = {}
            for field_value in obj.field_values.all():
                group_slug = field_value.field.group.slug
                field_slug = field_value.field.slug
                key = f"{group_slug}.{field_slug}"
                
                if field_value.field.field_type in ['file', 'image', 'video', 'audio'] and field_value.file:
                    custom_fields[key] = field_value.file.url
                else:
                    custom_fields[key] = field_value.value
            
            # Cria a versão
            PageVersion.objects.create(
                page=obj,
                title=obj.title,
                content=obj.content,
                summary=obj.summary,
                version_number=version_number,
                created_by=request.user,
                status=obj.status,
                meta_title=obj.meta_title,
                meta_description=obj.meta_description,
                meta_keywords=obj.meta_keywords,
                custom_fields=custom_fields,
                comment=_('Versão criada automaticamente após alterações')
            )
    
    def publish_pages(self, request, queryset):
        updated = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, _(f'{updated} pages were successfully published.'))
    publish_pages.short_description = _('Publish selected pages')

    def unpublish_pages(self, request, queryset):
        updated = queryset.update(status='draft', published_at=None)
        self.message_user(request, _(f'{updated} pages were successfully unpublished.'))
    unpublish_pages.short_description = _('Unpublish selected pages')
    
    def create_new_version(self, request, queryset):
        """
        Ação para criar uma nova versão manualmente.
        """
        for page in queryset:
            page.create_version(request.user, _("Manually created version"))
        self.message_user(request, _("New versions created successfully."))
    create_new_version.short_description = _("Create new version for selected pages")
    
    
    def get_urls(self):
        """Adiciona URLs personalizadas para ações administrativas"""
        urls = super().get_urls()
        custom_urls = [
            path('<int:page_id>/restore-version/<int:version_id>/', 
                 self.admin_site.admin_view(self.restore_version), 
                 name='pages_page_restore_version'),
            path('<int:page_id>/request-review/', 
                 self.admin_site.admin_view(self.request_review), 
                 name='pages_page_request_review'),
            path('<int:page_id>/publish/', 
                 self.admin_site.admin_view(self.publish_page), 
                 name='pages_page_publish'),
            path('<int:page_id>/unpublish/', 
                 self.admin_site.admin_view(self.unpublish_page), 
                 name='pages_page_unpublish'),
            path('<int:page_id>/archive/', 
                 self.admin_site.admin_view(self.archive_page), 
                 name='pages_page_archive'),
        ]
        return custom_urls + urls
    
    def restore_version(self, request, page_id, version_id):
        """Restaura uma versão específica da página"""
        page = get_object_or_404(Page, id=page_id)
        version = get_object_or_404(PageVersion, id=version_id, page=page)
        
        if request.method == 'POST':
            version.restore()
            self.message_user(request, _('Versão restaurada com sucesso.'), messages.SUCCESS)
            return HttpResponseRedirect(reverse('admin:pages_page_change', args=[page.id]))
            
        context = {
            'title': _('Restaurar Versão'),
            'page': page,
            'version': version,
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/pages/page/restore_version.html', context)
    
    def request_review(self, request, page_id):
        """Solicita revisão para uma página"""
        page = get_object_or_404(Page, id=page_id)
        
        if request.method == 'POST':
            comment = request.POST.get('comment', '')
            
            # Muda o status da página para 'em revisão'
            page.status = 'review'
            page.save(update_fields=['status'])
            
            # Cria a solicitação de revisão
            review_request = PageRevisionRequest.objects.create(
                page=page,
                requested_by=request.user,
                comment=comment,
                status='pending'
            )
            
            # Notifica os revisores (usuários com permissão de publicação)
            from django.contrib.auth.models import User, Permission
            from django.contrib.contenttypes.models import ContentType
            
            content_type = ContentType.objects.get_for_model(Page)
            publish_permission = Permission.objects.get(
                content_type=content_type, 
                codename='publish_page'
            )
            
            reviewers = User.objects.filter(
                is_staff=True,
                is_active=True,
                user_permissions=publish_permission
            ).exclude(id=request.user.id)
            
            for reviewer in reviewers:
                PageNotification.create_notification(
                    'revision_requested',
                    page,
                    reviewer,
                    request.user,
                    {'review_id': review_request.id}
                )
            
            self.message_user(request, _('Solicitação de revisão enviada com sucesso.'), messages.SUCCESS)
            return HttpResponseRedirect(reverse('admin:pages_page_change', args=[page.id]))
            
        context = {
            'title': _('Solicitar Revisão'),
            'page': page,
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/pages/page/request_review.html', context)
    
    def publish_page(self, request, page_id):
        """Publica uma página"""
        page = get_object_or_404(Page, id=page_id)
        
        if request.method == 'POST':
            # Atualiza o status e informações de publicação
            page.status = 'published'
            page.published_at = timezone.now()
            page.published_by = request.user
            page.save(update_fields=['status', 'published_at', 'published_by'])
            
            self.message_user(request, _('Página publicada com sucesso.'), messages.SUCCESS)
            return HttpResponseRedirect(reverse('admin:pages_page_change', args=[page.id]))
            
        context = {
            'title': _('Publicar Página'),
            'page': page,
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/pages/page/publish_page.html', context)
    
    def unpublish_page(self, request, page_id):
        """Despublica uma página (volta para rascunho)"""
        page = get_object_or_404(Page, id=page_id)
        
        if request.method == 'POST':
            # Atualiza o status
            page.status = 'draft'
            page.save(update_fields=['status'])
            
            self.message_user(request, _('Página despublicada com sucesso.'), messages.SUCCESS)
            return HttpResponseRedirect(reverse('admin:pages_page_change', args=[page.id]))
            
        context = {
            'title': _('Despublicar Página'),
            'page': page,
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/pages/page/unpublish_page.html', context)
    
    def archive_page(self, request, page_id):
        """Arquiva uma página"""
        page = get_object_or_404(Page, id=page_id)
        
        if request.method == 'POST':
            # Atualiza o status
            page.status = 'archived'
            page.save(update_fields=['status'])
            
            self.message_user(request, _('Página arquivada com sucesso.'), messages.SUCCESS)
            return HttpResponseRedirect(reverse('admin:pages_page_change', args=[page.id]))
            
        context = {
            'title': _('Arquivar Página'),
            'page': page,
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/pages/page/archive_page.html', context)
    
    def publish_selected(self, request, queryset):
        """Ação para publicar várias páginas selecionadas"""
        count = 0
        for page in queryset:
            if page.status != 'published':
                page.status = 'published'
                page.published_at = timezone.now()
                page.published_by = request.user
                page.save(update_fields=['status', 'published_at', 'published_by'])
                count += 1
                
        if count == 1:
            message = _('1 página foi publicada.')
        else:
            message = _('{} páginas foram publicadas.').format(count)
        self.message_user(request, message, messages.SUCCESS)
    publish_selected.short_description = _('Publicar páginas selecionadas')
    
    def unpublish_selected(self, request, queryset):
        """Ação para despublicar várias páginas selecionadas"""
        count = queryset.filter(status='published').update(status='draft')
        if count == 1:
            message = _('1 página foi despublicada.')
        else:
            message = _('{} páginas foram despublicadas.').format(count)
        self.message_user(request, message, messages.SUCCESS)
    unpublish_selected.short_description = _('Despublicar páginas selecionadas')
    
    def archive_selected(self, request, queryset):
        """Ação para arquivar várias páginas selecionadas"""
        count = queryset.update(status='archived')
        if count == 1:
            message = _('1 página foi arquivada.')
        else:
            message = _('{} páginas foram arquivadas.').format(count)
        self.message_user(request, message, messages.SUCCESS)
    archive_selected.short_description = _('Arquivar páginas selecionadas')


@admin.register(PageApproval)
class PageApprovalAdmin(admin.ModelAdmin):
    list_display = ('page', 'requested_by', 'requested_at', 'status', 'approved_by', 'approved_at')
    list_filter = ('status', 'requested_at', 'approved_at')
    search_fields = ('page__title', 'requested_by__username', 'approved_by__username')
    actions = ['approve_selected']

    def approve_selected(self, request, queryset):
        for approval in queryset.filter(status='pending'):
            approval.status = 'approved'
            approval.approved_by = request.user
            approval.approved_at = timezone.now()
            approval.save()
            approval.page.status = 'published'
            approval.page.save()
        self.message_user(request, _('Selected approvals have been processed.'))
    approve_selected.short_description = _('Approve selected requests')


class PageGalleryAdmin(admin.ModelAdmin):
    """Administração de galerias de imagens"""
    list_display = ('name', 'page', 'created_at', 'image_count')
    list_filter = ('created_at',)
    search_fields = ('name', 'description', 'page__title')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PageImageInline]
    
    def image_count(self, obj):
        """Retorna o número de imagens na galeria"""
        return obj.images.count()
    image_count.short_description = _('Imagens')


class PageRedirectAdmin(admin.ModelAdmin):
    """Administração de redirecionamentos"""
    list_display = ('old_path', 'page', 'new_path','redirect_type', 'is_active', 'access_count', 'last_accessed')
    list_filter = ('redirect_type', 'is_active', 'created_at')
    search_fields = ('old_path', 'new_path')
    readonly_fields = ('access_count', 'last_accessed')

    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-redirects/', self.import_redirects, name='import_redirects'),
            path('export-redirects/', self.export_redirects, name='export_redirects'),
        ]
        return custom_urls + urls

    def import_redirects(self, request):
        if request.method == 'POST':
            csv_file = request.FILES['csv_file']
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            for row in reader:
                PageRedirect.objects.create(
                    old_path=row['old_path'],
                    new_path=row['new_path'],
                    redirect_type=row['redirect_type']
                )
            messages.success(request, 'Redirects imported successfully.')
            return redirect('..')
        return render(request, 'admin/import_redirects.html')

    def export_redirects(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="redirects.csv"'
        writer = csv.writer(response)
        writer.writerow(['old_path', 'new_path', 'redirect_type'])
        for redirect in PageRedirect.objects.all():
            writer.writerow([redirect.old_path, redirect.new_path, redirect.redirect_type])
        return response

class PageCommentAdmin(admin.ModelAdmin):
    """Administração de comentários"""
    list_display = ('author_name', 'page', 'created_at', 'is_approved', 'likes', 'dislikes')
    list_filter = ('is_approved', 'created_at', 'is_pinned')
    search_fields = ('author_name', 'author_email', 'comment', 'page__title')
    readonly_fields = ('created_at', 'updated_at', 'ip_address', 'user_agent')
    actions = ['approve_comments', 'unapprove_comments']
    
    def approve_comments(self, request, queryset):
        """Ação para aprovar vários comentários"""
        count = queryset.update(is_approved=True)
        if count == 1:
            message = _('1 comentário foi aprovado.')
        else:
            message = _('{} comentários foram aprovados.').format(count)
        self.message_user(request, message, messages.SUCCESS)
    approve_comments.short_description = _('Aprovar comentários selecionados')
    
    def unapprove_comments(self, request, queryset):
        """Ação para desaprovar vários comentários"""
        count = queryset.update(is_approved=False)
        if count == 1:
            message = _('1 comentário foi desaprovado.')
        else:
            message = _('{} comentários foram desaprovados.').format(count)
        self.message_user(request, message, messages.SUCCESS)
    unapprove_comments.short_description = _('Desaprovar comentários selecionados')
    
    def get_urls(self):
        """Adiciona URLs personalizadas para ações administrativas"""
        urls = super().get_urls()
        custom_urls = [
            path('<int:comment_id>/approve/', 
                 self.admin_site.admin_view(self.approve_comment), 
                 name='pages_pagecomment_approve'),
        ]
        return custom_urls + urls
    
    def approve_comment(self, request, comment_id):
        """Aprova um comentário específico"""
        comment = get_object_or_404(PageComment, id=comment_id)
        comment.is_approved = True
        comment.save(update_fields=['is_approved'])
        
        self.message_user(request, _('Comentário aprovado com sucesso.'), messages.SUCCESS)
        return HttpResponseRedirect(reverse('admin:pages_pagecomment_changelist'))


class PageRevisionRequestAdmin(admin.ModelAdmin):
    """Administração de solicitações de revisão"""
    list_display = ('page', 'status', 'requested_by', 'reviewer', 'requested_at', 'completed_at')
    list_filter = ('status', 'requested_at', 'completed_at')
    search_fields = ('page__title', 'comment', 'reviewer_comment')
    readonly_fields = ('requested_at', 'completed_at')
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        """Ação para aprovar várias solicitações de revisão"""
        count = 0
        for review_request in queryset.filter(status='pending'):
            review_request.approve(reviewer=request.user)
            count += 1
            
        if count == 1:
            message = _('1 solicitação de revisão foi aprovada.')
        else:
            message = _('{} solicitações de revisão foram aprovadas.').format(count)
        self.message_user(request, message, messages.SUCCESS)
    approve_requests.short_description = _('Aprovar solicitações selecionadas')
    
    def reject_requests(self, request, queryset):
        """Ação para rejeitar várias solicitações de revisão"""
        count = 0
        for review_request in queryset.filter(status='pending'):
            review_request.reject(reviewer=request.user)
            count += 1
            
        if count == 1:
            message = _('1 solicitação de revisão foi rejeitada.')
        else:
            message = _('{} solicitações de revisão foram rejeitadas.').format(count)
        self.message_user(request, message, messages.SUCCESS)
    reject_requests.short_description = _('Rejeitar solicitações selecionadas')
    
    def get_urls(self):
        """Adiciona URLs personalizadas para ações administrativas"""
        urls = super().get_urls()
        custom_urls = [
            path('<int:request_id>/approve/', 
                 self.admin_site.admin_view(self.approve_revision), 
                 name='pages_pagerevisionrequest_approve'),
            path('<int:request_id>/reject/', 
                 self.admin_site.admin_view(self.reject_revision), 
                 name='pages_pagerevisionrequest_reject'),
        ]
        return custom_urls + urls
    
    def approve_revision(self, request, request_id):
        """Aprova uma solicitação de revisão específica"""
        revision_request = get_object_or_404(PageRevisionRequest, id=request_id)
        
        if request.method == 'POST':
            comment = request.POST.get('comment', '')
            revision_request.approve(reviewer=request.user, comment=comment)
            
            # Notifica o solicitante
            PageNotification.create_notification(
                'revision_approved',
                revision_request.page,
                revision_request.requested_by,
                request.user
            )
            
            self.message_user(request, _('Solicitação de revisão aprovada com sucesso.'), messages.SUCCESS)
            return HttpResponseRedirect(reverse('admin:pages_pagerevisionrequest_changelist'))
            
        context = {
            'title': _('Aprovar Solicitação de Revisão'),
            'revision_request': revision_request,
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/pages/pagerevisionrequest/approve_revision.html', context)
    
    def reject_revision(self, request, request_id):
        """Rejeita uma solicitação de revisão específica"""
        revision_request = get_object_or_404(PageRevisionRequest, id=request_id)
        
        if request.method == 'POST':
            comment = request.POST.get('comment', '')
            revision_request.reject(reviewer=request.user, comment=comment)
            
            # Notifica o solicitante
            PageNotification.create_notification(
                'revision_rejected',
                revision_request.page,
                revision_request.requested_by,
                request.user
            )
            
            self.message_user(request, _('Solicitação de revisão rejeitada com sucesso.'), messages.SUCCESS)
            return HttpResponseRedirect(reverse('admin:pages_pagerevisionrequest_changelist'))
            
        context = {
            'title': _('Rejeitar Solicitação de Revisão'),
            'revision_request': revision_request,
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/pages/pagerevisionrequest/reject_revision.html', context)


class PageNotificationAdmin(admin.ModelAdmin):
    """Administração de notificações"""
    list_display = ('user', 'notification_type', 'page', 'created_at', 'is_read')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('message', 'user__username', 'page__title')
    readonly_fields = ('notification_type', 'user', 'page', 'actor', 'message', 'created_at', 'read_at', 'extra_data')
    actions = ['mark_as_read', 'mark_as_unread']
    
    def has_add_permission(self, request):
        return False
    
    def mark_as_read(self, request, queryset):
        """Ação para marcar várias notificações como lidas"""
        now = timezone.now()
        count = queryset.filter(is_read=False).update(is_read=True, read_at=now)
        if count == 1:
            message = _('1 notificação foi marcada como lida.')
        else:
            message = _('{} notificações foram marcadas como lidas.').format(count)
        self.message_user(request, message, messages.SUCCESS)
    mark_as_read.short_description = _('Marcar como lidas')
    
    def mark_as_unread(self, request, queryset):
        """Ação para marcar várias notificações como não lidas"""
        count = queryset.filter(is_read=True).update(is_read=False, read_at=None)
        if count == 1:
            message = _('1 notificação foi marcada como não lida.')
        else:
            message = _('{} notificações foram marcadas como não lidas.').format(count)
        self.message_user(request, message, messages.SUCCESS)
    mark_as_unread.short_description = _('Marcar como não lidas')


# Registra os modelos no admin site
admin.site.register(PageCategory, PageCategoryAdmin)
admin.site.register(PageTemplate, PageTemplateAdmin)
admin.site.register(FieldGroup, FieldGroupAdmin)
admin.site.register(FieldDefinition, FieldDefinitionAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(PageGallery, PageGalleryAdmin)
admin.site.register(PageRedirect, PageRedirectAdmin)
admin.site.register(PageComment, PageCommentAdmin)
admin.site.register(PageRevisionRequest, PageRevisionRequestAdmin)
admin.site.register(PageNotification, PageNotificationAdmin)
