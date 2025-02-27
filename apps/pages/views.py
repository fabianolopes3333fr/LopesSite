# your_cms_app/pages/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import PermissionDenied
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.template.response import TemplateResponse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
import re

from .models import (
    Page, PageApproval, PageCategory, PageTemplate, FieldGroup, FieldDefinition, 
    PageFieldValue, PageGallery, PageImage, PageComment, PageVersion,
    PageRedirect, PageRevisionRequest, PageNotification, PageMeta, 
)
from .forms import (
    PageApprovalForm, PageBaseForm, PagePublishForm, PageReviewRequestForm, 
    PageCommentForm, PageSearchForm, GalleryForm
)

import json
import re

def handle_redirect(request, path):
    try:
        redirect_rule = PageRedirect.objects.get(old_path=path)
        redirect_rule.access_count += 1
        redirect_rule.last_accessed = timezone.now()
        redirect_rule.save()
        return redirect(redirect_rule.new_path, permanent=(redirect_rule.redirect_type == '301'))
    except PageRedirect.DoesNotExist:
        # Handle 404 or fallback to default view
        pass



@login_required
def compare_versions(request, page_id, version1_id, version2_id):
    """
    View para comparar duas versões de uma página.
    """
    page = get_object_or_404(Page, id=page_id)
    version1 = get_object_or_404(PageVersion, id=version1_id, page=page)
    version2 = get_object_or_404(PageVersion, id=version2_id, page=page)

    diff = page.get_version_diff(version1, version2)

    return render(request, 'pages/compare_versions.html', {
        'page': page,
        'version1': version1,
        'version2': version2,
        'diff': diff,
    })

@login_required
def restore_version(request, page_id, version_id):
    """
    View para restaurar uma versão específica de uma página.
    """
    page = get_object_or_404(Page, id=page_id)
    version = get_object_or_404(PageVersion, id=version_id, page=page)

    if request.method == 'POST':
        page.restore_version(version)
        messages.success(request, _("Page restored to version from %s") % version.created_at)
        return redirect('admin:pages_page_change', page.id)

    return render(request, 'pages/restore_version_confirm.html', {
        'page': page,
        'version': version,
    })

@login_required
@permission_required('pages.change_page')
def change_page_status(request, page_id):
    """
    View para alterar o status de uma página.
    """
    page = get_object_or_404(Page, id=page_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Page.STATUS_CHOICES):
            old_status = page.status
            page.status = new_status
            page.save()
            page.status_history.create(
                old_status=old_status,
                new_status=new_status,
                changed_by=request.user,
                comment=request.POST.get('comment', '')
            )
            messages.success(request, _('Page status updated successfully.'))
        else:
            messages.error(request, _('Invalid status.'))
    return redirect('admin:pages_page_change', page.id)

@login_required
@permission_required('pages.add_pageapproval')
def request_page_approval(request, page_id):
    """
    View para solicitar aprovação de uma página.
    """
    page = get_object_or_404(Page, id=page_id)
    if request.method == 'POST':
        form = PageApprovalForm(request.POST)
        if form.is_valid():
            approval = form.save(commit=False)
            approval.page = page
            approval.requested_by = request.user
            approval.save()
            messages.success(request, _('Approval request sent successfully.'))
            return redirect('admin:pages_page_change', page.id)
    else:
        form = PageApprovalForm()
    return render(request, 'admin/pages/page/approval_request.html', {'form': form, 'page': page})

@login_required
@permission_required('pages.change_pageapproval')
def approve_page(request, approval_id):
    """
    View para aprovar uma página.
    """
    approval = get_object_or_404(PageApproval, id=approval_id, status='pending')
    if request.method == 'POST':
        approval.status = 'approved'
        approval.approved_by = request.user
        approval.approved_at = timezone.now()
        approval.save()
        approval.page.status = 'published'
        approval.page.save()
        messages.success(request, _('Page approved and published successfully.'))
    return redirect('admin:pages_page_change', approval.page.id)

# classes ---------------------

class PageListView(ListView):
    """
    Exibe uma lista de páginas publicadas disponíveis para o público
    """
    model = Page
    template_name = 'pages/page_list.html'
    context_object_name = 'pages'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Page.objects.filter(status='published', visibility='public')
        
        # Filtra com base na categoria, se especificada
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            queryset = queryset.filter(categories__slug=category_slug)
        
        # Busca por texto, se especificada
        query = self.request.GET.get('q', '')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | 
                Q(content__icontains=query) | 
                Q(summary__icontains=query) |
                Q(meta_keywords__icontains=query)
            )
            
        # Filtra por data, se especificada
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(published_at__gte=date_from)
            
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(published_at__lte=date_to)
        
        # Otimização de consulta
        queryset = queryset.select_related('template', 'parent')
        queryset = queryset.prefetch_related('categories')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Adiciona o formulário de busca
        initial = {}
        if 'q' in self.request.GET:
            initial['q'] = self.request.GET['q']
        if 'date_from' in self.request.GET:
            initial['date_from'] = self.request.GET['date_from']
        if 'date_to' in self.request.GET:
            initial['date_to'] = self.request.GET['date_to']
            
        context['search_form'] = PageSearchForm(initial=initial)
        
        # Adiciona a categoria atual, se aplicável
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['current_category'] = get_object_or_404(PageCategory, slug=category_slug)
        
        # Adiciona todas as categorias para o menu lateral
        context['categories'] = PageCategory.objects.filter(is_active=True)
        
        # Adiciona páginas em destaque ou recentes
        context['featured_pages'] = Page.objects.filter(
            status='published', 
            visibility='public'
        ).order_by('-published_at')[:5]
        
        return context


class PageDetailView(DetailView):
    """
    Exibe uma página individual
    """
    model = Page
    template_name = 'pages/page_detail.html'
    context_object_name = 'page'
    
    def get_object(self, queryset=None):
        """
        Recupera o objeto da página usando o slug ou o caminho completo
        """
        if queryset is None:
            queryset = self.get_queryset()
            
        # Tenta obter por slug direto
        slug = self.kwargs.get('slug')
        if slug:
            return get_object_or_404(queryset, slug=slug)
            
        # Tenta obter por caminho (para páginas aninhadas)
        path = self.kwargs.get('path')
        if path:
            slugs = path.split('/')
            last_slug = slugs[-1]
            
            # Filtra apenas as páginas que têm o último slug
            queryset = queryset.filter(slug=last_slug)
            
            # Verificações adicionais para garantir que o caminho completo corresponda
            for page in queryset:
                ancestors = list(page.get_ancestors())
                ancestors.append(page)  # Inclui a própria página
                
                # Verifica se os slugs dos ancestrais correspondem ao caminho
                ancestor_slugs = [ancestor.slug for ancestor in ancestors]
                if '/'.join(ancestor_slugs) == path:
                    return page
            
            # Se não encontrou uma correspondência exata, levanta 404
            raise Http404(_("Página não encontrada."))
        
        # Se não houver slug nem path, levanta 404
        raise Http404(_("Página não encontrada."))
    
    def get_queryset(self):
        """
        Retorna o queryset otimizado para a página
        """
        queryset = Page.objects.all()
        
        # Otimizações de consulta
        queryset = queryset.select_related('template', 'parent', 'created_by', 'published_by')
        queryset = queryset.prefetch_related(
            'categories',
            'field_values__field__group',
            'galleries__images',
            Prefetch('comments', queryset=PageComment.objects.filter(is_approved=True, parent=None))
        )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = self.object
        
        # Verifica se a página está publicada ou se o usuário tem permissão para visualizá-la
        if not page.is_published():
            if not self.request.user.is_authenticated or not self.request.user.has_perm('pages.view_page'):
                if page.status == 'scheduled' and page.scheduled_at:
                    messages.info(self.request, _("Esta página será publicada em {}.").format(page.scheduled_at))
                else:
                    raise Http404(_("Página não encontrada ou não publicada."))
        
        # Verifica se a página é protegida por senha
        if page.visibility == 'password' and page.password:
            session_key = f'page_password_{page.id}'
            
            # Se a senha ainda não foi fornecida
            if session_key not in self.request.session:
                context['password_required'] = True
                return context
        
        # Prepara campos customizados
        context['custom_fields'] = self.prepare_custom_fields(page)
        
        # Prepara o formulário de comentários, se os comentários estiverem habilitados
        if page.enable_comments:
            context['comment_form'] = PageCommentForm(page=page, user=self.request.user)
            
            # Carrega comentários aprovados
            comments = page.comments.filter(is_approved=True, parent=None).order_by('-created_at')
            context['comments'] = comments
            
            # Carrega respostas para cada comentário
            for comment in comments:
                comment.replies_list = comment.replies.filter(is_approved=True).order_by('created_at')
        
        # Carrega versões da página para usuários com permissão
        if self.request.user.is_authenticated and self.request.user.has_perm('pages.view_pageversion'):
            context['versions'] = page.versions.order_by('-version_number')[:5]
        
        # Carrega páginas irmãs (mesma parent) para navegação
        if page.parent:
            siblings = page.parent.get_children().filter(status='published', visibility='public')
            context['siblings'] = siblings
            
            # Encontrar página anterior e próxima
            siblings_list = list(siblings)
            try:
                page_index = siblings_list.index(page)
                if page_index > 0:
                    context['prev_page'] = siblings_list[page_index - 1]
                if page_index < len(siblings_list) - 1:
                    context['next_page'] = siblings_list[page_index + 1]
            except ValueError:
                # A página não foi encontrada na lista (pode acontecer se não estiver publicada)
                pass
        
        # Carrega as subpáginas (filhas)
        context['children'] = page.get_children().filter(status='published', visibility='public')
        
        # Aumenta o contador de visualizações
        self.increment_page_views(page)
        
        # Processa os metadados para templates
        context.update(self.prepare_metadata(page))
        
        return context
    
    def prepare_custom_fields(self, page):
        """
        Prepara os campos customizados para exibição
        """
        # Agrupa campos por grupo
        fields_by_group = {}
        
        for field_value in page.field_values.all():
            group = field_value.field.group
            if group.id not in fields_by_group:
                fields_by_group[group.id] = {
                    'group': group,
                    'fields': []
                }
            
            # Processa o valor de acordo com o tipo de campo
            display_value = field_value.get_value_display()
            
            # Para imagens
            if field_value.field.field_type == 'image' and field_value.file:
                display_value = {
                    'url': field_value.file.url,
                    'alt': field_value.field.name
                }
            
            # Adiciona o field_value à lista
            fields_by_group[group.id]['fields'].append({
                'field': field_value.field,
                'value': field_value.value,
                'display_value': display_value,
                'file': field_value.file
            })
        
        # Ordena os grupos e campos
        result = []
        for group_data in fields_by_group.values():
            group_data['fields'].sort(key=lambda x: x['field'].order)
            result.append(group_data)
        
        result.sort(key=lambda x: x['group'].order)
        
        return result
    
    def prepare_metadata(self, page):
        """
        Prepara metadados para os templates
        """
        metadata = {
            'meta_title': page.effective_meta_title,
            'meta_description': page.meta_description or page.summary,
            'meta_keywords': page.meta_keywords,
            'og_title': page.effective_og_title,
            'og_description': page.effective_og_description,
            'og_image': page.og_image.url if page.og_image else None,
            'og_type': page.og_type,
            'schema_json': json.dumps(page.get_schema_json())
        }
        
        return metadata
    
    def increment_page_views(self, page):
        """
        Incrementa o contador de visualizações da página
        """
        # Verifica se já visualizou nesta sessão para evitar contagens duplicadas
        session_key = f'viewed_page_{page.id}'
        if session_key not in self.request.session:
            # Registra a visualização na sessão
            self.request.session[session_key] = True
            
            # Incrementa o contador no meta
            try:
                meta = PageMeta.objects.get(page=page, key='view_count')
                meta.value = str(int(meta.value) + 1)
                meta.save()
            except PageMeta.DoesNotExist:
                # Se não existir, cria com valor inicial 1
                PageMeta.objects.create(page=page, key='view_count', value='1')
            except (ValueError, TypeError):
                # Se o valor não for numérico, reinicia com 1
                meta = PageMeta.objects.get(page=page, key='view_count')
                meta.value = '1'
                meta.save()
    
    def post(self, request, *args, **kwargs):
        """
        Processa solicitações POST, como envio de comentários ou verificação de senha
        """
        self.object = self.get_object()
        page = self.object
        
        # Verifica se a página é protegida por senha
        if page.visibility == 'password' and page.password:
            session_key = f'page_password_{page.id}'
            
            # Se for uma tentativa de senha
            if 'password' in request.POST:
                password = request.POST.get('password')
                if page.check_password(password):
                    # Senha correta, armazena na sessão
                    request.session[session_key] = True
                    return redirect(request.path)
                else:
                    # Senha incorreta
                    messages.error(request, _("Senha incorreta. Por favor, tente novamente."))
                    return self.get(request, *args, **kwargs)
        
        # Processa comentários
        if page.enable_comments and 'comment' in request.POST:
            form = PageCommentForm(request.POST, page=page, user=request.user, request=request)
            
            # Processa comentário-resposta
            if 'parent_id' in request.POST and request.POST['parent_id']:
                try:
                    parent_id = int(request.POST['parent_id'])
                    parent = PageComment.objects.get(id=parent_id, page=page)
                    form.parent = parent
                except (ValueError, PageComment.DoesNotExist):
                    pass
            
            if form.is_valid():
                comment = form.save()
                
                if comment.is_approved:
                    messages.success(request, _("Seu comentário foi publicado com sucesso."))
                else:
                    messages.info(request, _("Seu comentário foi enviado e está aguardando aprovação."))
                
                return redirect(request.path)
            else:
                # Se o formulário for inválido, renderiza a página com o formulário e erros
                context = self.get_context_data(object=page)
                context['comment_form'] = form
                return self.render_to_response(context)
        
        # Se chegou até aqui, é uma requisição POST não tratada
        return self.get(request, *args, **kwargs)


class PageVersionDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Exibe uma versão específica de uma página permitindo comparação com a versão atual
    """
    model = PageVersion
    template_name = 'pages/page_version_detail.html'
    context_object_name = 'version'
    permission_required = 'pages.view_pageversion'
    
    def get_object(self, queryset=None):
        """
        Recupera a versão específica da página
        """
        if queryset is None:
            queryset = self.get_queryset()
            
        page_id = self.kwargs.get('page_id')
        version_number = self.kwargs.get('version_number')
        
        # Obtém a página e verifica se existe
        page = get_object_or_404(Page, id=page_id)
        
        # Verifica se o usuário tem permissão para ver a página
        if page.visibility == 'private' and (not self.request.user.is_authenticated or 
                                            not self.request.user.has_perm('pages.view_page')):
            raise PermissionDenied(_("Você não tem permissão para visualizar esta página."))
            
        # Obtém a versão específica
        return get_object_or_404(queryset, page=page, version_number=version_number)
    
    def get_queryset(self):
        """
        Retorna o queryset otimizado para a versão
        """
        return PageVersion.objects.select_related('page', 'created_by')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        version = self.object
        
        # Adiciona a página original
        context['page'] = version.page
        
        # Se houver campos personalizados salvos
        if version.custom_fields:
            # Converte para formato legível
            formatted_fields = []
            for key, value in version.custom_fields.items():
                try:
                    group_slug, field_slug = key.split('.')
                    group = FieldGroup.objects.get(slug=group_slug, template=version.page.template)
                    field = FieldDefinition.objects.get(slug=field_slug, group=group)
                    
                    formatted_fields.append({
                        'group': group.name,
                        'field': field.name,
                        'value': value
                    })
                except (ValueError, FieldGroup.DoesNotExist, FieldDefinition.DoesNotExist):
                    # Se não conseguir encontrar o campo, mantém o formato original
                    formatted_fields.append({
                        'key': key,
                        'value': value
                    })
            
            context['custom_fields'] = formatted_fields
        
        # Para comparação com a versão atual
        context['current_version'] = version.page.versions.order_by('-version_number').first()
        
        return context


class PageCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Cria uma nova página
    """
    model = Page
    form_class = PageBaseForm
    template_name = 'pages/page_form.html'
    permission_required = 'pages.add_page'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        
        # Pré-seleciona o template, se especificado
        template_id = self.request.GET.get('template')
        if template_id:
            try:
                template = PageTemplate.objects.get(id=template_id, is_active=True)
                initial['template'] = template
            except PageTemplate.DoesNotExist:
                pass
                
        # Pré-seleciona a categoria, se especificada
        category_id = self.request.GET.get('category')
        if category_id:
            try:
                category = PageCategory.objects.get(id=category_id, is_active=True)
                initial['categories'] = [category]
            except PageCategory.DoesNotExist:
                pass
        
        # Pré-seleciona a página pai, se especificada
        parent_id = self.request.GET.get('parent')
        if parent_id:
            try:
                parent = Page.objects.get(id=parent_id)
                initial['parent'] = parent
            except Page.DoesNotExist:
                pass
        
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Disponibiliza templates e categorias para o formulário
        context['available_templates'] = PageTemplate.objects.filter(is_active=True)
        context['available_categories'] = PageCategory.objects.filter(is_active=True)
        
        # Verifica permissões
        context['can_publish'] = self.request.user.has_perm('pages.publish_page')
        
        return context
    
    def form_valid(self, form):
        """
        Processa o formulário válido e salva a página
        """
        # Salva a página
        page = form.save()
        
        messages.success(self.request, _("Página criada com sucesso."))
        
        # Redireciona para a página de edição para adicionar campos personalizados
        return redirect('pages:page_update', pk=page.pk)


class PageUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Atualiza uma página existente
    """
    model = Page
    form_class = PageBaseForm
    template_name = 'pages/page_form.html'
    permission_required = 'pages.change_page'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = self.object
        
        # Disponibiliza templates e categorias para o formulário
        context['available_templates'] = PageTemplate.objects.filter(is_active=True)
        context['available_categories'] = PageCategory.objects.filter(is_active=True)
        
        # Verifica permissões
        context['can_publish'] = self.request.user.has_perm('pages.publish_page')
        
        # Adiciona galerias e campos personalizados
        context['galleries'] = page.galleries.all()
        
        # Se estiver no modo de alteração de template
        if 'change_template' in self.request.GET:
            context['change_template'] = True
            context['warning_message'] = _("Atenção: Alterar o template pode resultar na perda de campos personalizados.")
        
        return context
    
    def form_valid(self, form):
        """
        Processa o formulário válido e salva a página
        """
        # Verifica se o template foi alterado
        if 'template' in form.changed_data:
            old_template = self.object.template
            new_template = form.cleaned_data['template']
            
            # Se realmente houve mudança
            if old_template != new_template:
                # Guarda um registro dos valores antigos antes de potencialmente perdê-los
                old_values = {}
                for field_value in self.object.field_values.all():
                    key = f"{field_value.field.group.slug}.{field_value.field.slug}"
                    if field_value.field.field_type in ['file', 'image', 'video', 'audio'] and field_value.file:
                        old_values[key] = field_value.file.url
                    else:
                        old_values[key] = field_value.value
                
                # Cria uma versão com os campos antigos antes de alterá-los
                version_number = 1
                last_version = PageVersion.objects.filter(page=self.object).order_by('-version_number').first()
                if last_version:
                    version_number = last_version.version_number + 1
                
                PageVersion.objects.create(
                    page=self.object,
                    title=self.object.title,
                    content=self.object.content,
                    summary=self.object.summary,
                    version_number=version_number,
                    created_by=self.request.user,
                    status=self.object.status,
                    meta_title=self.object.meta_title,
                    meta_description=self.object.meta_description,
                    meta_keywords=self.object.meta_keywords,
                    custom_fields=old_values,
                    comment=_("Versão criada automaticamente antes da alteração de template")
                )
                
                # Limpa os valores de campos personalizados antigos
                # Isso é necessário porque os campos do template antigo 
                # não existem mais no novo template
                self.object.field_values.all().delete()
        
        # Salva a página
        page = form.save()
        
        messages.success(self.request, _("Página atualizada com sucesso."))
        
        # Define o próximo url com base nos parâmetros da requisição
        next_url = self.request.GET.get('next')
        if next_url and next_url.startswith('/'):  # Previne open redirect
            return redirect(next_url)
        else:
            return redirect('pages:page_update', pk=page.pk)


class PageDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Exclui uma página
    """
    model = Page
    template_name = 'pages/page_confirm_delete.html'
    permission_required = 'pages.delete_page'
    context_object_name = 'page'
    
    def get_success_url(self):
        messages.success(self.request, _("Página excluída com sucesso."))
        return reverse('pages:page_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = self.object
        
        # Verifica se a página possui filhos
        context['has_children'] = page.get_children().exists()
        
        return context
    
    def delete(self, request, *args, **kwargs):
        page = self.get_object()
        
        # Verifica se a página tem filhos
        if page.get_children().exists():
            messages.error(request, _("Esta página possui subpáginas. Exclua ou mova as subpáginas primeiro."))
            return redirect('pages:page_update', pk=page.pk)
        
        # Continua com a exclusão
        return super().delete(request, *args, **kwargs)


@method_decorator(csrf_protect, name='dispatch')
class PagePublishView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """
    Publica uma página que estava em rascunho ou revisão
    """
    form_class = PagePublishForm
    template_name = 'pages/page_publish.html'
    permission_required = 'pages.publish_page'
    
    def dispatch(self, request, *args, **kwargs):
        # Verifica se a página já está publicada
        page_id = self.kwargs.get('pk')
        page = get_object_or_404(Page, id=page_id)
        
        if page.status == 'published':
            messages.info(request, _("Esta página já está publicada."))
            return redirect('pages:page_update', pk=page.id)


class PageUnpublishView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Despublica uma página (muda o status para rascunho)
    """
    permission_required = 'pages.publish_page'
    
    def get(self, request, pk):
        page = get_object_or_404(Page, id=pk)
        
        # Verifica se a página está publicada
        if page.status != 'published':
            messages.info(request, _("Esta página não está publicada."))
            return redirect('pages:page_update', pk=page.id)
        
        context = {
            'page': page,
        }
        return render(request, 'pages/page_unpublish.html', context)
    
    @transaction.atomic
    def post(self, request, pk):
        page = get_object_or_404(Page, id=pk)
        
        # Verifica se a página está publicada
        if page.status != 'published':
            messages.info(request, _("Esta página não está publicada."))
            return redirect('pages:page_update', pk=page.id)
        
        # Muda o status para rascunho
        page.status = 'draft'
        page.save(update_fields=['status'])
        
        # Cria uma versão
        comment = request.POST.get('comment', '')
        version_number = 1
        last_version = PageVersion.objects.filter(page=page).order_by('-version_number').first()
        if last_version:
            version_number = last_version.version_number + 1
        
        PageVersion.objects.create(
            page=page,
            title=page.title,
            content=page.content,
            summary=page.summary,
            version_number=version_number,
            created_by=request.user,
            status='draft',
            meta_title=page.meta_title,
            meta_description=page.meta_description,
            meta_keywords=page.meta_keywords,
            comment=comment or _("Página despublicada por {}").format(request.user.get_full_name() or request.user.username)
        )
        
        # Notifica o autor da página se for diferente
        if page.created_by and page.created_by != request.user:
            PageNotification.create_notification(
                'page_updated',
                page,
                page.created_by,
                request.user,
                {'action': 'unpublish'}
            )
        
        messages.success(request, _("Página despublicada com sucesso."))
        return redirect('pages:page_update', pk=page.id)


class PageArchiveView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Arquiva uma página (muda o status para arquivado)
    """
    permission_required = 'pages.archive_page'
    
    def get(self, request, pk):
        page = get_object_or_404(Page, id=pk)
        
        context = {
            'page': page,
        }
        return render(request, 'pages/page_archive.html', context)
    
    @transaction.atomic
    def post(self, request, pk):
        page = get_object_or_404(Page, id=pk)
        
        # Muda o status para arquivado
        page.status = 'archived'
        page.save(update_fields=['status'])
        
        # Cria uma versão
        comment = request.POST.get('comment', '')
        version_number = 1
        last_version = PageVersion.objects.filter(page=page).order_by('-version_number').first()
        if last_version:
            version_number = last_version.version_number + 1
        
        PageVersion.objects.create(
            page=page,
            title=page.title,
            content=page.content,
            summary=page.summary,
            version_number=version_number,
            created_by=request.user,
            status='archived',
            meta_title=page.meta_title,
            meta_description=page.meta_description,
            meta_keywords=page.meta_keywords,
            comment=comment or _("Página arquivada por {}").format(request.user.get_full_name() or request.user.username)
        )
        
        # Notifica o autor da página se for diferente
        if page.created_by and page.created_by != request.user:
            PageNotification.create_notification(
                'page_archived',
                page,
                page.created_by,
                request.user
            )
        
        messages.success(request, _("Página arquivada com sucesso."))
        return redirect('pages:page_list')


class PageVersionRestoreView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Restaura uma versão específica de uma página
    """
    permission_required = 'pages.change_page'
    
    def get(self, request, page_id, version_id):
        page = get_object_or_404(Page, id=page_id)
        version = get_object_or_404(PageVersion, id=version_id, page=page)
        
        context = {
            'page': page,
            'version': version,
        }
        return render(request, 'pages/page_version_restore.html', context)
    
    @transaction.atomic
    def post(self, request, page_id, version_id):
        page = get_object_or_404(Page, id=page_id)
        version = get_object_or_404(PageVersion, id=version_id, page=page)
        
        # Restaura a versão
        version.restore()
        
        # Atualiza o usuário que fez a alteração
        page.updated_by = request.user
        page.save(update_fields=['updated_by'])
        
        messages.success(request, _("Versão {} restaurada com sucesso.").format(version.version_number))
        return redirect('pages:page_update', pk=page.id)


class PageRevisionReviewView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Permite revisar uma solicitação de revisão de página
    """
    permission_required = 'pages.publish_page'
    
    def get(self, request, pk):
        review_request = get_object_or_404(PageRevisionRequest, id=pk, status='pending')
        page = review_request.page
        
        context = {
            'review_request': review_request,
            'page': page,
        }
        return render(request, 'pages/page_revision_review.html', context)
    
    @transaction.atomic
    def post(self, request, pk):
        review_request = get_object_or_404(PageRevisionRequest, id=pk, status='pending')
        page = review_request.page
        
        action = request.POST.get('action')
        comment = request.POST.get('comment', '')
        
        if action == 'approve':
            # Aprova a solicitação
            review_request.approve(reviewer=request.user, comment=comment)
            
            # Atualiza a página para publicada
            page.status = 'published'
            page.published_at = timezone.now()
            page.published_by = request.user
            page.save(update_fields=['status', 'published_at', 'published_by'])
            
            # Notifica o solicitante
            PageNotification.create_notification(
                'revision_approved',
                page,
                review_request.requested_by,
                request.user
            )
            
            messages.success(request, _("Solicitação de revisão aprovada com sucesso."))
        elif action == 'reject':
            # Rejeita a solicitação
            review_request.reject(reviewer=request.user, comment=comment)
            
            # Volta o status da página para rascunho
            page.status = 'draft'
            page.save(update_fields=['status'])
            
            # Notifica o solicitante
            PageNotification.create_notification(
                'revision_rejected',
                page,
                review_request.requested_by,
                request.user
            )
            
            messages.success(request, _("Solicitação de revisão rejeitada."))
        
        return redirect('pages:page_list')


class GalleryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Cria uma nova galeria para uma página
    """
    model = PageGallery
    form_class = GalleryForm
    template_name = 'pages/gallery_form.html'
    permission_required = 'pages.add_pagegallery'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        # Obtém a página associada
        page_id = self.kwargs.get('page_id')
        page = get_object_or_404(Page, id=page_id)
        kwargs['page'] = page
        
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Adiciona a página ao contexto
        page_id = self.kwargs.get('page_id')
        context['page'] = get_object_or_404(Page, id=page_id)
        
        return context
    
    def get_success_url(self):
        return reverse('pages:gallery_update', kwargs={'pk': self.object.pk})


class GalleryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Atualiza uma galeria existente
    """
    model = PageGallery
    form_class = GalleryForm
    template_name = 'pages/gallery_form.html'
    permission_required = 'pages.change_pagegallery'
    context_object_name = 'gallery'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['page'] = self.object.page
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Adiciona a página e as imagens ao contexto
        context['page'] = self.object.page
        context['images'] = self.object.images.all().order_by('order')
        
        return context
    
    def get_success_url(self):
        messages.success(self.request, _("Galeria atualizada com sucesso."))
        return reverse('pages:gallery_update', kwargs={'pk': self.object.pk})


class GalleryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Exclui uma galeria
    """
    model = PageGallery
    template_name = 'pages/gallery_confirm_delete.html'
    permission_required = 'pages.delete_pagegallery'
    context_object_name = 'gallery'
    
    def get_success_url(self):
        messages.success(self.request, _("Galeria excluída com sucesso."))
        return reverse('pages:page_update', kwargs={'pk': self.object.page.pk})


@login_required
@permission_required('pages.add_pageimage')
def gallery_upload_image(request, gallery_id):
    """
    View para upload de imagens para uma galeria
    """
    gallery = get_object_or_404(PageGallery, id=gallery_id)
    
    if request.method == 'POST':
        # Processa o upload de imagem
        image = request.FILES.get('image')
        title = request.POST.get('title', '')
        alt_text = request.POST.get('alt_text', '')
        
        if image:
            # Determina a ordem da nova imagem
            order = 0
            last_image = PageImage.objects.filter(gallery=gallery).order_by('-order').first()
            if last_image:
                order = last_image.order + 1
            
            # Cria a imagem
            PageImage.objects.create(
                gallery=gallery,
                image=image,
                title=title or image.name,
                alt_text=alt_text,
                order=order
            )
            
            messages.success(request, _("Imagem adicionada com sucesso."))
        else:
            messages.error(request, _("Nenhuma imagem enviada."))
    
    return redirect('pages:gallery_update', pk=gallery.pk)


@login_required
@permission_required('pages.change_pageimage')
def gallery_update_image(request, image_id):
    """
    View para atualizar informações de uma imagem
    """
    image = get_object_or_404(PageImage, id=image_id)
    
    if request.method == 'POST':
        # Atualiza os dados da imagem
        image.title = request.POST.get('title', image.title)
        image.alt_text = request.POST.get('alt_text', image.alt_text)
        image.order = int(request.POST.get('order', image.order))
        image.save()
        
        messages.success(request, _("Imagem atualizada com sucesso."))
    
    return redirect('pages:gallery_update', pk=image.gallery.pk)


@login_required
@permission_required('pages.delete_pageimage')
def gallery_delete_image(request, image_id):
    """
    View para excluir uma imagem
    """
    image = get_object_or_404(PageImage, id=image_id)
    gallery = image.gallery
    
    if request.method == 'POST':
        image.delete()
        messages.success(request, _("Imagem excluída com sucesso."))
    
    return redirect('pages:gallery_update', pk=gallery.pk)


@login_required
@permission_required('pages.change_pageimage')
def gallery_reorder_images(request, gallery_id):
    """
    View para reordenar imagens em uma galeria via AJAX
    """
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            gallery = get_object_or_404(PageGallery, id=gallery_id)
            order_data = json.loads(request.body)
            
            with transaction.atomic():
                for item in order_data:
                    image_id = item.get('id')
                    new_order = item.get('order')
                    
                    if image_id and new_order is not None:
                        PageImage.objects.filter(id=image_id, gallery=gallery).update(order=new_order)
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
@permission_required('pages.change_page')
def page_check_slug(request):
    """
    Verifica se um slug já está em uso (via AJAX)
    """
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        slug = request.GET.get('slug', '')
        page_id = request.GET.get('page_id')
        
        if not slug:
            return JsonResponse({'valid': False, 'message': _('Slug não pode estar vazio.')})
        
        # Verifica se o slug é válido
        if not re.match(r'^[a-z0-9][-a-z0-9]*$', slug):
            return JsonResponse({'valid': False, 'message': _('Slug inválido. Use apenas letras minúsculas, números e hífens.')})
        
        # Verifica se o slug já está em uso
        existing_page = Page.objects.filter(slug=slug).exclude(id=page_id).first()
        if existing_page:
            return JsonResponse({'valid': False, 'message': _('Este slug já está em uso.')})
        
        return JsonResponse({'valid': True})
    
    return JsonResponse({'valid': False, 'message': _('Requisição inválida.')}, status=400)
    


@method_decorator(csrf_protect, name='dispatch')
class PagePublishView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """
    Publica uma página
    """
    permission_required = 'pages.publish_page'
    form_class = PagePublishForm
    template_name = 'pages/page_publish.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_id = self.kwargs.get('pk')
        context['page'] = get_object_or_404(Page, id=page_id)
        return context
    
    def form_valid(self, form):
        page_id = self.kwargs.get('pk')
        page = get_object_or_404(Page, id=page_id)
        
        # Atualiza o status para publicado
        page.status = 'published'
        page.published_at = timezone.now()
        page.published_by = self.request.user
        page.save(update_fields=['status', 'published_at', 'published_by'])
        
        # Cria uma versão com o comentário da publicação
        comment = form.cleaned_data.get('comment', '')
        version_number = 1
        last_version = PageVersion.objects.filter(page=page).order_by('-version_number').first()
        if last_version:
            version_number = last_version.version_number + 1
        
        PageVersion.objects.create(
            page=page,
            title=page.title,
            content=page.content,
            summary=page.summary,
            version_number=version_number,
            created_by=self.request.user,
            status='published',
            meta_title=page.meta_title,
            meta_description=page.meta_description,
            meta_keywords=page.meta_keywords,
            comment=comment or _("Página publicada por {}").format(self.request.user.get_full_name() or self.request.user.username)
        )
        
        # Atualiza as solicitações de revisão pendentes
        for request in PageRevisionRequest.objects.filter(page=page, status='pending'):
            request.approve(reviewer=self.request.user, comment=_("Aprovado durante publicação"))
            
            # Notifica o solicitante
            PageNotification.create_notification(
                'revision_approved',
                page,
                request.requested_by,
                self.request.user
            )
        
        # Notifica o autor da página se for diferente do publicador
        if page.created_by and page.created_by != self.request.user:
            PageNotification.create_notification(
                'page_published',
                page,
                page.created_by,
                self.request.user
            )
        
        messages.success(self.request, _("Página '{}' publicada com sucesso.").format(page.title))
        # Redireciona para a visualização da página
        return redirect(page.get_absolute_url())


