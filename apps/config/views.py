# apps/config/views.py
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from .models import Page, SiteStyle, Menu, PageVersionConfig, CustomField, FieldGroup
from .forms import PageForm, SiteStyleForm, MenuForm, CustomFieldForm, FieldGroupForm
from django.core.exceptions import ValidationError
from utils.validators import validate_css
from mptt.utils import get_cached_trees
import cssutils
import logging


logger = logging.getLogger('config')

ITEMS_PER_PAGE = 10

#@login_required
#@permission_required('config.dashboard_view_config')
def dashboard_view_config(request):
    """
    Dashboard principal do sistema de configuração
    """
    context = {
        'total_pages': Page.objects.count(),
        'published_pages': Page.objects.filter(status='published').count(),
        'total_menus': Menu.objects.count(),
        'recent_pages': Page.objects.order_by('-created_at')[:5]
    }
    return render(request, 'config/dashboard.html', context)

#@login_required
#@permission_required('config.page_list')
def page_list(request):
    """
    Lista todas as páginas com paginação
    """
    page_list = Page.objects.all().order_by('-created_at')
    paginator = Paginator(page_list, ITEMS_PER_PAGE)
    
    page = request.GET.get('page')
    try:
        pages = paginator.page(page)
    except PageNotAnInteger:
        pages = paginator.page(1)
    except EmptyPage:
        pages = paginator.page(paginator.num_pages)
    
    return render(request, 'config/pages/page_list.html', {'pages': pages})

#@login_required
#@permission_required('config.page_create')
def page_create(request):
    """
    Cria uma nova página
    """
    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            page = form.save(commit=False)
            page.created_by = request.user
            page.updated_by = request.user
            page.save()
            messages.success(request, _('Page créée avec succès.'))
            return redirect('page_detail', slug=page.slug)
    else:
        form = PageForm()
    
    return render(request, 'config/pages/page_form.html', {
        'form': form,
        'title': _('Créer une nouvelle page')
    })

#@login_required
#@permission_required('config.page_update')
def page_update(request, slug):
    """
    Edita uma página existente
    """
    page = get_object_or_404(Page, slug=slug)
    if request.method == 'POST':
        form = PageForm(request.POST, instance=page)
        if form.is_valid():
            # Criar versão antes de atualizar
            PageVersionConfig.objects.create(
                page=page,
                content=page.content,
                created_by=request.user,
                comment=_("Version automatique")
            )
            
            page = form.save(commit=False)
            page.updated_by = request.user
            page.save()
            
            messages.success(request, _('Page mise à jour avec succès.'))
            return redirect('page_detail', slug=page.slug)
    else:
        form = PageForm(instance=page)
    
    return render(request, 'config/pages/page_form.html', {
        'form': form,
        'page': page,
        'title': _('Modifier la page')
    })


#@login_required
#@permission_required('config.page_delete')
def page_delete(request, slug):
    page = get_object_or_404(Page, slug=slug)
    if request.method == 'POST':
        logger.info(f"Page '{page.title}' supprimée par {request.user}")
        page.delete()
        messages.success(request, _('Page supprimée avec succès.'))
        return redirect('page_list')
    return render(request, 'config/pages/page_confirm_delete.html', {'page': page})

def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug)
    if page.status != 'published' and not request.user.is_staff:
        return redirect('page_list')
    return render(request, 'config/pages/page_detail.html', {'page': page})



#@login_required
def custom_field_create(request, page_slug):
    page = get_object_or_404(Page, slug=page_slug)
    if request.method == 'POST':
        form = CustomFieldForm(request.POST)
        if form.is_valid():
            custom_field = form.save(commit=False)
            custom_field.page = page
            custom_field.save()
            return redirect('page_edit', slug=page.slug)
    else:
        form = CustomFieldForm()
    return render(request, 'config/custom/custom_field_form.html', {'form': form, 'page': page})


#@login_required
def field_group_create(request, page_slug):
    page = get_object_or_404(Page, slug=page_slug)
    if request.method == 'POST':
        form = FieldGroupForm(request.POST)
        if form.is_valid():
            field_group = form.save(commit=False)
            field_group.page = page
            field_group.save()
            return redirect('page_edit', slug=page.slug)
    else:
        form = FieldGroupForm()
    return render(request, 'config/custom/field_group_form.html', {'form': form, 'page': page})

#@login_required
#@permission_required('config.style_list')
#@cache_page(60 * 15)
def style_list(request):
    """
    Lista todos os estilos
    """
    styles = SiteStyle.objects.all()
    return render(request, 'config/styles/list.html', {'styles': styles})


#@login_required
#@permission_required('config.style_create')
def style_create(request):
    """
    Cria um novo estilo
    """
    if request.method == 'POST':
        form = SiteStyleForm(request.POST)
        if form.is_valid():
            try:
                # Validar CSS personalizado
                if form.cleaned_data['custom_css']:
                    validate_css.parseString(form.cleaned_data['custom_css'])
                style = form.save()
                messages.success(request, _('Nouveau style créé avec succès.'))
                return redirect('config:style_list')
            except Exception as e:
                messages.error(request, _('CSS invalide: {}').format(str(e)))
    else:
        form = SiteStyleForm()

    return render(request, 'config/styles/form.html', {
        'form': form,
        'title': _('Créer un nouveau style')
    })

#@login_required
#@permission_required('config.style_update')
def style_update(request, pk):
    """
    Atualiza um estilo existente
    """
    style = get_object_or_404(SiteStyle, pk=pk)
    if request.method == 'POST':
        form = SiteStyleForm(request.POST, instance=style)
        if form.is_valid():
            try:
                # Validar CSS personalizado
                if form.cleaned_data['custom_css']:
                    validate_css(form.cleaned_data['custom_css'])
                style = form.save()
                messages.success(request, _('Style mis à jour avec succès.'))
                return redirect('config:style_list')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, _('Une erreur s\'est produite lors de la mise à jour du style.'))
                logger.error(f"Erreur de mise à jour du style: {str(e)}")
    else:
        form = SiteStyleForm(instance=style)
    
    return render(request, 'config/styles/form.html', {
        'form': form,
        'style': style,
        'title': _('Modifier le style')
    })
#@login_required
#@permission_required('config.style_delete')
def style_delete(request, pk):
    """
    Exclui um estilo
    """
    style = get_object_or_404(SiteStyle, pk=pk)
    if request.method == 'POST':
        style.delete()
        messages.success(request, _('Style supprimé avec succès.'))
        return redirect('config:style_list')
    return render(request, 'config/styles/delete.html', {'style': style})

#@login_required
#@permission_required('config.menu_list')
def menu_list(request):
    """
    Lista e gerencia os menus
    """
    menus = Menu.objects.all().order_by('tree_id', 'lft')  # Usando ordem MPTT padrão
    pages = Page.objects.filter(status='published')
    
    if request.method == 'POST':
        form = MenuForm(request.POST)
        if form.is_valid():
            menu = form.save()
            messages.success(request, _('Menu créé avec succès.'))
            return redirect('config:menu_list')
    else:
        form = MenuForm()

    return render(request, 'config/menus/list.html', {
        'menus': menus,
        'pages': pages,
        'form': form
    })


#@login_required
#@permission_required('config.menu_create')
def menu_create(request):
    """
    Cria os menus
    """
    if request.method == 'POST':
        form = MenuForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Menu créé avec succès.'))
            return redirect('config:menu_list')
    else:
        form = MenuForm()
    
    return render(request, 'config/menus/create.html', {'form': form})
#@login_required
#@permission_required('config.menu_update')
def menu_update(request, pk):
    """
    Edita os menus
    """
    menu = get_object_or_404(Menu, pk=pk)
    if request.method == 'POST':
        form = MenuForm(request.POST, instance=menu)
        if form.is_valid():
            form.save()
            messages.success(request, _('Menu mis à jour avec succès.'))
            return redirect('config:menu_list')
    else:
        form = MenuForm(instance=menu)
    return render(request, 'config/menus/form.html', {'form': form, 'menu': menu})

#@login_required
#@permission_required('config.menu_delete')
def menu_delete(request, pk):
    menu = get_object_or_404(Menu, pk=pk)
    if request.method == 'POST':
        menu.delete()
        messages.success(request, _('Menu supprimé avec succès.'))
        return redirect('config:menu_list')
    return render(request, 'config/menus/delete.html', {'menu': menu})

#@login_required
@require_POST
def menu_order(request):
    """
    Atualiza a ordem dos menus
    """
    order = request.POST.getlist('order[]')
    menus = Menu.objects.all()
    for menu in menus:
        menu.order = order.index(str(menu.pk))  # Use 'pk' em vez de 'id'
        menu.save()
    return JsonResponse({'status': 'success'})