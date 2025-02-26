import json
import csv
import yaml
import os
import zipfile
import tempfile
import re
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.files import File
from django.conf import settings
from django.utils.text import slugify
from django.db import transaction
from io import StringIO, BytesIO
from ..pages.models import (
    Page, PageCategory, PageTemplate, FieldGroup, FieldDefinition, 
    PageFieldValue, PageGallery, PageImage, PageMeta
)


class ImportResult:
    """Classe para armazenar resultados de importação"""
    
    def __init__(self):
        self.created = []
        self.updated = []
        self.skipped = []
        self.errors = []
        self.total = 0
    
    def add_created(self, item):
        """Adiciona um item criado"""
        self.created.append(item)
        self.total += 1
    
    def add_updated(self, item):
        """Adiciona um item atualizado"""
        self.updated.append(item)
        self.total += 1
    
    def add_skipped(self, item, reason):
        """Adiciona um item ignorado"""
        self.skipped.append({
            'item': item,
            'reason': reason
        })
        self.total += 1
    
    def add_error(self, item, error):
        """Adiciona um erro de importação"""
        self.errors.append({
            'item': item,
            'error': str(error)
        })
        self.total += 1
    
    def summary(self):
        """Retorna um resumo da importação"""
        return {
            'total': self.total,
            'created': len(self.created),
            'updated': len(self.updated),
            'skipped': len(self.skipped),
            'errors': len(self.errors)
        }


class BaseImporter:
    """Classe base para importadores de conteúdo"""
    
    def __init__(self, data, user=None, options=None):
        self.data = data
        self.user = user
        self.options = options or {}
        self.result = ImportResult()
        self.temp_dir = None
    
    def prepare_import(self):
        """Prepara os dados para importação"""
        pass
    
    def import_data(self):
        """Importa os dados"""
        self.prepare_import()
        return self.result
    
    def clean_up(self):
        """Limpa recursos temporários após a importação"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)


class JSONImporter(BaseImporter):
    """Importador para formato JSON"""
    
    def prepare_import(self):
        """Prepara os dados para importação a partir de JSON"""
        try:
            # Converte string JSON para dicionário, se necessário
            if isinstance(self.data, str):
                self.data = json.loads(self.data)
            
            # Verifica se o arquivo tem a estrutura esperada
            if 'pages' not in self.data:
                raise ValueError("Formato JSON inválido: 'pages' não encontrado")
            
            # Importa as páginas
            self._import_pages(self.data['pages'])
            
        except json.JSONDecodeError as e:
            self.result.add_error("JSON parsing", f"Erro ao analisar JSON: {str(e)}")
        except Exception as e:
            self.result.add_error("Import process", f"Erro na importação: {str(e)}")
    
    @transaction.atomic
    def _import_pages(self, pages_data):
        """Importa as páginas a partir dos dados JSON"""
        for page_data in pages_data:
            try:
                # Valida dados mínimos
                if 'title' not in page_data or 'slug' not in page_data:
                    self.result.add_error(page_data.get('title', 'Unknown'), 
                                         "Título ou slug ausente")
                    continue
                
                # Verifica se a página já existe
                existing_page = Page.objects.filter(slug=page_data['slug']).first()
                
                # Determina a ação com base nas opções
                if existing_page:
                    action = self.options.get('duplicate_action', 'skip')
                    
                    if action == 'skip':
                        self.result.add_skipped(page_data['title'], "Página já existe")
                        continue
                    elif action == 'update':
                        page = self._update_page(existing_page, page_data)
                        self.result.add_updated(page.title)
                    elif action == 'create_new':
                        # Gera um novo slug
                        page_data['slug'] = self._generate_unique_slug(page_data['slug'])
                        page = self._create_page(page_data)
                        self.result.add_created(page.title)
                else:
                    # Cria uma nova página
                    page = self._create_page(page_data)
                    self.result.add_created(page.title)
            
            except Exception as e:
                self.result.add_error(page_data.get('title', 'Unknown'), str(e))
    
    def _create_page(self, page_data):
        """Cria uma nova página com base nos dados JSON"""
        # Obtém o template
        template = None
        if 'template' in page_data and page_data['template']:
            template = PageTemplate.objects.filter(slug=page_data['template']).first()
            if not template:
                raise ValueError(f"Template '{page_data['template']}' não encontrado")
        
        # Obtém a página pai
        parent = None
        if 'parent' in page_data and page_data['parent']:
            parent = Page.objects.filter(slug=page_data['parent']).first()
            if not parent:
                raise ValueError(f"Página pai '{page_data['parent']}' não encontrada")
        
        # Cria a página base
        page = Page(
            title=page_data['title'],
            slug=page_data['slug'],
            content=page_data.get('content', ''),
            summary=page_data.get('summary', ''),
            status=page_data.get('status', 'draft'),
            meta_title=page_data.get('meta_title', ''),
            meta_description=page_data.get('meta_description', ''),
            meta_keywords=page_data.get('meta_keywords', ''),
            template=template,
            parent=parent,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Salva a página para obter um ID
        page.save()
        
        # Adiciona categorias
        if 'categories' in page_data:
            for category_slug in page_data['categories']:
                category = PageCategory.objects.filter(slug=category_slug).first()
                if category:
                    page.categories.add(category)
        
        # Adiciona campos personalizados
        if 'fields' in page_data and template:
            self._process_custom_fields(page, template, page_data['fields'])
        
        # Adiciona metadados
        if 'meta' in page_data:
            for key, value in page_data['meta'].items():
                PageMeta.objects.create(page=page, key=key, value=value)
        
        # Processa galerias
        if 'galleries' in page_data:
            self._process_galleries(page, page_data['galleries'])
        
        return page
    
    def _update_page(self, page, page_data):
        """Atualiza uma página existente com base nos dados JSON"""
        # Atualiza os campos básicos
        page.title = page_data['title']
        if 'content' in page_data:
            page.content = page_data['content']
        if 'summary' in page_data:
            page.summary = page_data['summary']
        if 'status' in page_data:
            page.status = page_data['status']
        if 'meta_title' in page_data:
            page.meta_title = page_data['meta_title']
        if 'meta_description' in page_data:
            page.meta_description = page_data['meta_description']
        if 'meta_keywords' in page_data:
            page.meta_keywords = page_data['meta_keywords']
        
        # Atualiza o template se fornecido
        if 'template' in page_data and page_data['template']:
            template = PageTemplate.objects.filter(slug=page_data['template']).first()
            if template:
                page.template = template
        
        # Atualiza a página pai se fornecida
        if 'parent' in page_data:
            if page_data['parent']:
                parent = Page.objects.filter(slug=page_data['parent']).first()
                if parent and parent != page and not parent.is_descendant_of(page):
                    page.parent = parent
            else:
                page.parent = None
        
        # Atualiza o criador se solicitado
        if self.options.get('update_author', False) and 'created_by' in page_data:
            created_by_username = page_data.get('created_by')
            if created_by_username:
                user = User.objects.filter(username=created_by_username).first()
                if user:
                    page.created_by = user
        
        # Define o usuário atual como o atualizador
        page.updated_by = self.user
        
        # Salva as alterações
        page.save()
        
        # Atualiza categorias se fornecidas
        if 'categories' in page_data:
            page.categories.clear()
            for category_slug in page_data['categories']:
                category = PageCategory.objects.filter(slug=category_slug).first()
                if category:
                    page.categories.add(category)
        
        # Processa campos personalizados se fornecidos
        if 'fields' in page_data and page.template:
            # Remove campos existentes se solicitado
            if self.options.get('replace_fields', False):
                PageFieldValue.objects.filter(page=page).delete()
            
            # Adiciona novos campos
            self._process_custom_fields(page, page.template, page_data['fields'])
        
        # Processa metadados
        if 'meta' in page_data:
            # Remove metadados existentes se solicitado
            if self.options.get('replace_meta', False):
                PageMeta.objects.filter(page=page).delete()
            
            # Adiciona/atualiza metadados
            for key, value in page_data['meta'].items():
                meta, created = PageMeta.objects.update_or_create(
                    page=page, key=key, defaults={'value': value}
                )
        
        # Processa galerias
        if 'galleries' in page_data:
            # Remove galerias existentes se solicitado
            if self.options.get('replace_galleries', False):
                # Remove primeiro as imagens para evitar referências órfãs
                for gallery in page.galleries.all():
                    PageImage.objects.filter(gallery=gallery).delete()
                page.galleries.all().delete()
            
            # Adiciona/atualiza galerias
            self._process_galleries(page, page_data['galleries'])
        
        return page
    
    def _process_custom_fields(self, page, template, fields_data):
        """Processa os campos personalizados"""
        for group_slug, fields in fields_data.items():
            # Busca o grupo de campos
            try:
                field_group = FieldGroup.objects.get(template=template, slug=group_slug)
            except FieldGroup.DoesNotExist:
                continue
            
            # Processa cada campo
            for field_slug, field_data in fields.items():
                try:
                    # Busca a definição do campo
                    field_def = FieldDefinition.objects.get(group=field_group, slug=field_slug)
                    
                    # Determina o valor e arquivo
                    if isinstance(field_data, dict):
                        value = field_data.get('value', '')
                        field_type = field_data.get('type', field_def.field_type)
                    else:
                        value = field_data
                        field_type = field_def.field_type
                    
                    # Verifica se já existe um valor para este campo
                    try:
                        field_value = PageFieldValue.objects.get(page=page, field=field_def)
                        field_value.value = value
                    except PageFieldValue.DoesNotExist:
                        field_value = PageFieldValue(page=page, field=field_def, value=value)
                    
                    # Trata campos do tipo arquivo
                    if field_type in ['file', 'image', 'video', 'audio'] and isinstance(field_data, dict):
                        file_path = field_data.get('value', '')
                        if file_path and os.path.exists(file_path):
                            with open(file_path, 'rb') as f:
                                file_name = os.path.basename(file_path)
                                field_value.file.save(file_name, File(f), save=False)
                    
                    # Salva o valor do campo
                    field_value.save()
                    
                except FieldDefinition.DoesNotExist:
                    continue
    
    def _process_galleries(self, page, galleries_data):
        """Processa as galerias de imagens"""
        for gallery_data in galleries_data:
            # Busca a galeria ou cria uma nova
            gallery, created = PageGallery.objects.get_or_create(
                page=page, 
                slug=gallery_data.get('slug', slugify(gallery_data['name'])),
                defaults={
                    'name': gallery_data['name'],
                    'description': gallery_data.get('description', ''),
                    'created_by': self.user
                }
            )
            
            # Processa as imagens da galeria
            if 'images' in gallery_data:
                for image_data in gallery_data['images']:
                    file_path = image_data.get('file_url', '')
                    if file_path and os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            file_name = image_data.get('file_name', os.path.basename(file_path))
                            # Cria a imagem
                            image = PageImage(
                                gallery=gallery,
                                title=image_data.get('title', file_name),
                                alt_text=image_data.get('alt_text', ''),
                                description=image_data.get('description', ''),
                                order=image_data.get('order', 0)
                            )
                            image.image.save(file_name, File(f), save=True)
    
    def _generate_unique_slug(self, base_slug):
        """Gera um slug único baseado no original"""
        slug = base_slug
        counter = 1
        while Page.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug


class CSVImporter(BaseImporter):
    """Importador para formato CSV"""
    
    def prepare_import(self):
        """Prepara os dados para importação a partir de CSV"""
        try:
            # Converte string CSV para linhas, se necessário
            if isinstance(self.data, str):
                csv_data = StringIO(self.data)
                reader = csv.reader(csv_data)
            else:
                reader = csv.reader(self.data)
            
            # Lê o cabeçalho
            headers = next(reader)
            
            # Normaliza cabeçalhos para corresponder aos nomes de campo
            normalized_headers = [h.lower().replace(' ', '_') for h in headers]
            
            # Prepara os dados das páginas
            pages_data = []
            for row in reader:
                page_data = {}
                for i, value in enumerate(row):
                    if i < len(normalized_headers):
                        page_data[normalized_headers[i]] = value
                
                if 'title' in page_data and page_data['title']:
                    pages_data.append(page_data)
            
            # Importa as páginas
            with transaction.atomic():
                self._import_pages(pages_data)
            
        except csv.Error as e:
            self.result.add_error("CSV parsing", f"Erro ao analisar CSV: {str(e)}")
        except Exception as e:
            self.result.add_error("Import process", f"Erro na importação: {str(e)}")
    
    def _import_pages(self, pages_data):
        """Importa as páginas a partir dos dados CSV"""
        for page_data in pages_data:
            try:
                # Valida dados mínimos
                if 'title' not in page_data:
                    self.result.add_error("Unknown", "Título ausente")
                    continue
                
                # Gera um slug se necessário
                if 'slug' not in page_data or not page_data['slug']:
                    page_data['slug'] = slugify(page_data['title'])
                
                # Verifica se a página já existe
                existing_page = Page.objects.filter(slug=page_data['slug']).first()
                
                # Determina a ação com base nas opções
                if existing_page:
                    action = self.options.get('duplicate_action', 'skip')
                    
                    if action == 'skip':
                        self.result.add_skipped(page_data['title'], "Página já existe")
                        continue
                    elif action == 'update':
                        page = self._update_page(existing_page, page_data)
                        self.result.add_updated(page.title)
                    elif action == 'create_new':
                        # Gera um novo slug
                        page_data['slug'] = self._generate_unique_slug(page_data['slug'])
                        page = self._create_page(page_data)
                        self.result.add_created(page.title)
                else:
                    # Cria uma nova página
                    page = self._create_page(page_data)
                    self.result.add_created(page.title)
            
            except Exception as e:
                self.result.add_error(page_data.get('title', 'Unknown'), str(e))
    
    def _create_page(self, page_data):
        """Cria uma nova página com base nos dados CSV"""
        # Obtém o template
        template = None
        if 'template' in page_data and page_data['template']:
            template = PageTemplate.objects.filter(slug=page_data['template']).first()
        
        # Obtém a página pai
        parent = None
        if 'parent' in page_data and page_data['parent']:
            parent = Page.objects.filter(slug=page_data['parent']).first()
        
        # Cria a página base
        page = Page(
            title=page_data['title'],
            slug=page_data['slug'],
            content=page_data.get('content', ''),
            summary=page_data.get('summary', ''),
            status=page_data.get('status', 'draft'),
            meta_title=page_data.get('meta_title', ''),
            meta_description=page_data.get('meta_description', ''),
            meta_keywords=page_data.get('meta_keywords', ''),
            template=template,
            parent=parent,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Salva a página para obter um ID
        page.save()
        
        # Adiciona categorias se fornecidas
        if 'categories' in page_data and page_data['categories']:
            for category_slug in page_data['categories'].split(','):
                category_slug = category_slug.strip()
                category = PageCategory.objects.filter(slug=category_slug).first()
                if category:
                    page.categories.add(category)
        
        return page
    
    def _update_page(self, page, page_data):
        """Atualiza uma página existente com base nos dados CSV"""
        # Atualiza os campos básicos
        page.title = page_data['title']
        if 'content' in page_data:
            page.content = page_data['content']
        if 'summary' in page_data:
            page.summary = page_data['summary']
        if 'status' in page_data:
            page.status = page_data['status']
        if 'meta_title' in page_data:
            page.meta_title = page_data['meta_title']
        if 'meta_description' in page_data:
            page.meta_description = page_data['meta_description']
        if 'meta_keywords' in page_data:
            page.meta_keywords = page_data['meta_keywords']
        
        # Atualiza o template se fornecido
        if 'template' in page_data and page_data['template']:
            template = PageTemplate.objects.filter(slug=page_data['template']).first()
            if template:
                page.template = template
        
        # Atualiza a página pai se fornecida
        if 'parent' in page_data:
            if page_data['parent']:
                parent = Page.objects.filter(slug=page_data['parent']).first()
                if parent and parent != page and not parent.is_descendant_of(page):
                    page.parent = parent
            else:
                page.parent = None
        
        # Atualiza o criador se solicitado
        if self.options.get('update_author', False) and 'created_by' in page_data:
            created_by_username = page_data.get('created_by')
            if created_by_username:
                user = User.objects.filter(username=created_by_username).first()
                if user:
                    page.created_by = user
        
        # Define o usuário atual como o atualizador
        page.updated_by = self.user
        
        # Salva as alterações
        page.save()
        
        # Atualiza categorias se fornecidas
        if 'categories' in page_data and page_data['categories']:
            if self.options.get('replace_categories', False):
                page.categories.clear()
            
            for category_slug in page_data['categories'].split(','):
                category_slug = category_slug.strip()
                category = PageCategory.objects.filter(slug=category_slug).first()
                if category:
                    page.categories.add(category)
        
        return page
    
    def _generate_unique_slug(self, base_slug):
        """Gera um slug único baseado no original"""
        slug = base_slug
        counter = 1
        while Page.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug


class ZipImporter(BaseImporter):
    """Importador para formato ZIP com JSON e arquivos"""
    
    def prepare_import(self):
        """Prepara os dados para importação a partir de ZIP"""
        try:
            # Cria um diretório temporário para extrair os arquivos
            self.temp_dir = tempfile.mkdtemp()
            
            # Abre o arquivo ZIP
            with zipfile.ZipFile(BytesIO(self.data), 'r') as zip_file:
                # Extrai todos os arquivos para o diretório temporário
                zip_file.extractall(self.temp_dir)
                
                # Procura pelo arquivo JSON principal
                json_file_path = os.path.join(self.temp_dir, 'pages.json')
                if not os.path.exists(json_file_path):
                    # Procura por qualquer arquivo JSON
                    json_files = [f for f in os.listdir(self.temp_dir) if f.endswith('.json')]
                    if json_files:
                        json_file_path = os.path.join(self.temp_dir, json_files[0])
                    else:
                        raise ValueError("Arquivo JSON não encontrado no arquivo ZIP")
                
                # Lê o arquivo JSON
                with open(json_file_path, 'r', encoding='utf-8') as json_file:
                    json_data = json.load(json_file)
                
                # Atualiza caminhos de arquivos para apontar para os arquivos extraídos
                if 'pages' in json_data:
                    self._update_file_paths(json_data['pages'])
                
                # Cria um importador JSON
                json_importer = JSONImporter(json_data, self.user, self.options)
                
                # Importa os dados
                json_importer.import_data()
                
                # Copia os resultados
                self.result = json_importer.result
        
        except zipfile.BadZipFile as e:
            self.result.add_error("ZIP parsing", f"Arquivo ZIP inválido: {str(e)}")
        except Exception as e:
            self.result.add_error("Import process", f"Erro na importação: {str(e)}")
    
    def _update_file_paths(self, pages_data):
        """Atualiza os caminhos de arquivos para apontar para os arquivos extraídos"""
        for page_data in pages_data:
            # Atualiza a imagem OG
            if 'og_image' in page_data and page_data['og_image']:
                file_path = page_data['og_image']
                local_path = os.path.join(self.temp_dir, 'media', file_path.lstrip('/'))
                if os.path.exists(local_path):
                    page_data['og_image'] = local_path
            
            # Atualiza campos personalizados
            if 'fields' in page_data:
                for group_slug, fields in page_data['fields'].items():
                    for field_slug, field_data in fields.items():
                        if isinstance(field_data, dict) and 'value' in field_data:
                            file_path = field_data['value']
                            if file_path.startswith('/') or '://' not in file_path:
                                local_path = os.path.join(self.temp_dir, 'media', file_path.lstrip('/'))
                                if os.path.exists(local_path):
                                    field_data['value'] = local_path
            
            # Atualiza galerias
            if 'galleries' in page_data:
                for gallery_data in page_data['galleries']:
                    if 'images' in gallery_data:
                        for image_data in gallery_data['images']:
                            if 'file_url' in image_data:
                                file_path = image_data['file_url']
                                if file_path.startswith('/') or '://' not in file_path:
                                    local_path = os.path.join(self.temp_dir, 'media', file_path.lstrip('/'))
                                    if os.path.exists(local_path):
                                        image_data['file_url'] = local_path
    
    def clean_up(self):
        """Limpa o diretório temporário após a importação"""
        super().clean_up()