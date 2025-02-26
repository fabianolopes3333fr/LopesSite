# your_cms_app/importexport/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.utils.text import slugify
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime
import json

from ..pages.models import Page, PageCategory
from .exporters import (
    JSONExporter, XMLExporter, CSVExporter, YAMLExporter, ZipExporter
)
from .importers import (
    JSONImporter, CSVImporter, ZipImporter
)


@login_required
@permission_required('pages.view_page')
def export_list(request):
    """Exibe a lista de páginas para exportação"""
    # Obtém filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    category = request.GET.get('category', '')
    
    # Filtra páginas
    pages = Page.objects.all()
    
    if search:
        pages = pages.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search) |
            Q(summary__icontains=search)
        )
    
    if status:
        pages = pages.filter(status=status)
    
    if category:
        pages = pages.filter(categories__slug=category)
    
    # Ordena e pagina os resultados
    pages = pages.order_by('title')
    paginator = Paginator(pages, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'category': category,
        'categories': PageCategory.objects.all(),
        'status_choices': Page.STATUS_CHOICES,
    }
    
    return render(request, 'importexport/export_list.html', context)


@login_required
@permission_required('pages.view_page')
def export_selected(request):
    """Exporta as páginas selecionadas"""
    if request.method != 'POST':
        return redirect('importexport:export_list')
    
    # Obtém os IDs das páginas selecionadas
    selected_ids = request.POST.getlist('selected_pages')
    
    if not selected_ids:
        messages.warning(request, "Nenhuma página selecionada para exportação.")
        return redirect('importexport:export_list')
    
    # Obtém as páginas selecionadas
    pages = Page.objects.filter(id__in=selected_ids)
    
    # Obtém o formato de exportação
    export_format = request.POST.get('export_format', 'json')
    
    # Cria o exportador adequado
    if export_format == 'json':
        exporter = JSONExporter(pages, request.user)
    elif export_format == 'xml':
        exporter = XMLExporter(pages, request.user)
    elif export_format == 'csv':
        exporter = CSVExporter(pages, request.user)
    elif export_format == 'yaml':
        exporter = YAMLExporter(pages, request.user)
    elif export_format == 'zip':
        exporter = ZipExporter(pages, request.user)
    else:
        messages.error(request, f"Formato de exportação '{export_format}' não suportado.")
        return redirect('importexport:export_list')
    
    # Realiza a exportação
    exported_data = exporter.export()
    
    # Define o nome do arquivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"pages_export_{timestamp}.{export_format}"
    
    # Define o tipo de conteúdo
    content_types = {
        'json': 'application/json',
        'xml': 'application/xml',
        'csv': 'text/csv',
        'yaml': 'application/x-yaml',
        'zip': 'application/zip'
    }
    content_type = content_types.get(export_format, 'application/octet-stream')
    
    # Cria a resposta HTTP
    response = HttpResponse(exported_data, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Limpa arquivos temporários
    exporter.clean_temp_files()
    
    return response


@login_required
@permission_required('pages.add_page')
def import_form(request):
    """Exibe o formulário para importação de páginas"""
    context = {
        'page_templates': Page.objects.all(),
        'categories': PageCategory.objects.all(),
    }
    
    return render(request, 'importexport/import_form.html', context)


@login_required
@permission_required('pages.add_page')
def import_preview(request):
    """Pré-visualiza a importação de páginas"""
    if request.method != 'POST':
        return redirect('importexport:import_form')
    
    # Obtém o arquivo enviado
    import_file = request.FILES.get('import_file')
    
    if not import_file:
        messages.error(request, "Nenhum arquivo enviado.")
        return redirect('importexport:import_form')
    
    # Identifica o formato do arquivo
    file_ext = os.path.splitext(import_file.name)[1].lower()
    
    # Lê o conteúdo do arquivo
    file_content = import_file.read()
    
    # Tenta importar o arquivo para pré-visualização
    try:
        # Cria o importador adequado
        if file_ext == '.json':
            importer = JSONImporter(file_content, request.user, {'duplicate_action': 'skip'})
        elif file_ext == '.csv':
            importer = CSVImporter(file_content, request.user, {'duplicate_action': 'skip'})
        elif file_ext == '.zip':
            importer = ZipImporter(file_content, request.user, {'duplicate_action': 'skip'})
        else:
            messages.error(request, f"Formato de arquivo '{file_ext}' não suportado.")
            return redirect('importexport:import_form')
        
        # Realiza a pré-visualização da importação
        importer.prepare_import()
        
        # Armazena o conteúdo do arquivo na sessão para importação posterior
        request.session['import_file_content'] = file_content.decode('utf-8') if isinstance(file_content, bytes) else file_content
        request.session['import_file_format'] = file_ext
        
        # Conta páginas existentes e novas
        existing_pages = sum(1 for page in importer.data.get('pages', []) if Page.objects.filter(slug=page.get('slug', '')).exists())
        new_pages = len(importer.data.get('pages', [])) - existing_pages
        
        context = {
            'preview': True,
            'existing_pages': existing_pages,
            'new_pages': new_pages,
            'total_pages': len(importer.data.get('pages', [])),
            'file_name': import_file.name,
            'file_size': import_file.size,
            'pages_preview': importer.data.get('pages', [])[:10],  # Mostra até 10 páginas na pré-visualização
        }
        
        # Limpa recursos temporários
        importer.clean_up()
        
        return render(request, 'importexport/import_preview.html', context)
        
    except Exception as e:
        messages.error(request, f"Erro ao processar o arquivo: {str(e)}")
        return redirect('importexport:import_form')


@login_required
@permission_required('pages.add_page')
def import_process(request):
    """Realiza a importação de páginas"""
    if request.method != 'POST':
        return redirect('importexport:import_form')
    
    # Obtém o conteúdo do arquivo da sessão
    file_content = request.session.get('import_file_content')
    file_format = request.session.get('import_file_format')
    
    if not file_content or not file_format:
        messages.error(request, "Nenhum arquivo para importação.")
        return redirect('importexport:import_form')
    
    # Obtém as opções de importação
    options = {
        'duplicate_action': request.POST.get('duplicate_action', 'skip'),
        'update_author': request.POST.get('update_author') == 'on',
        'replace_fields': request.POST.get('replace_fields') == 'on',
        'replace_meta': request.POST.get('replace_meta') == 'on',
        'replace_galleries': request.POST.get('replace_galleries') == 'on',
        'replace_categories': request.POST.get('replace_categories') == 'on',
    }
    
    # Cria o importador adequado
    try:
        if file_format == '.json':
            importer = JSONImporter(file_content, request.user, options)
        elif file_format == '.csv':
            importer = CSVImporter(file_content, request.user, options)
        elif file_format == '.zip':
            # Para arquivos ZIP, precisamos converter novamente para bytes
            if isinstance(file_content, str):
                file_content = file_content.encode('utf-8')
            importer = ZipImporter(file_content, request.user, options)
        else:
            messages.error(request, f"Formato de arquivo '{file_format}' não suportado.")
            return redirect('importexport:import_form')
        
        # Realiza a importação
        result = importer.import_data()
        
        # Limpa recursos temporários
        importer.clean_up()
        
        # Limpa dados da sessão
        del request.session['import_file_content']
        del request.session['import_file_format']
        
        # Exibe mensagem de sucesso com resumo
        summary = result.summary()
        messages.success(
            request, 
            f"Importação concluída: {summary['created']} páginas criadas, "
            f"{summary['updated']} atualizadas, {summary['skipped']} ignoradas, "
            f"{summary['errors']} erros."
        )
        
        # Redireciona para a lista de páginas
        return redirect('pages:page_list')
        
    except Exception as e:
        messages.error(request, f"Erro ao importar: {str(e)}")
        return redirect('importexport:import_form')
