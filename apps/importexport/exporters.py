import json
import csv
import yaml
import os
import zipfile
import tempfile
from django.utils import timezone
from django.contrib.auth.models import User
from django.core import serializers
from django.conf import settings
from django.utils.text import slugify
from io import StringIO, BytesIO
from ..pages.models import (
    Page, PageCategory, PageTemplate, FieldGroup, FieldDefinition, 
    PageFieldValue, PageGallery, PageImage, PageMeta
)


class BaseExporter:
    """Classe base para exportadores de conteúdo"""
    
    def __init__(self, queryset=None, user=None):
        self.queryset = queryset or []
        self.user = user
        self.export_date = timezone.now()
        self.exported_data = {}
        self.temp_files = []
    
    def prepare_export(self):
        """Prepara os dados para exportação"""
        pass
    
    def export(self):
        """Exporta os dados no formato específico"""
        self.prepare_export()
        return self.get_export_data()
    
    def get_export_data(self):
        """Retorna os dados exportados no formato apropriado"""
        return self.exported_data
    
    def clean_temp_files(self):
        """Limpa arquivos temporários criados durante a exportação"""
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        self.temp_files = []


class JSONExporter(BaseExporter):
    """Exportador para formato JSON"""
    
    def prepare_export(self):
        """Prepara os dados para exportação em JSON"""
        pages_data = []
        
        for page in self.queryset:
            # Dados básicos da página
            page_data = {
                'id': page.id,
                'title': page.title,
                'slug': page.slug,
                'content': page.content,
                'summary': page.summary,
                'status': page.status,
                'created_at': page.created_at.isoformat(),
                'updated_at': page.updated_at.isoformat(),
                'published_at': page.published_at.isoformat() if page.published_at else None,
                'meta_title': page.meta_title,
                'meta_description': page.meta_description,
                'meta_keywords': page.meta_keywords,
                'created_by': page.created_by.username if page.created_by else None,
                'template': page.template.slug if page.template else None,
                'parent': page.parent.slug if page.parent else None,
                'categories': [cat.slug for cat in page.categories.all()],
            }
            
            # Campos personalizados
            page_data['fields'] = self._get_custom_fields(page)
            
            # Metadados adicionais
            page_data['meta'] = self._get_meta_items(page)
            
            # Galerias
            page_data['galleries'] = self._get_galleries(page)
            
            pages_data.append(page_data)
        
        # Dados de exportação
        export_info = {
            'export_date': self.export_date.isoformat(),
            'exporter': self.user.username if self.user else 'anonymous',
            'version': '1.0',
            'count': len(pages_data)
        }
        
        # Montagem final dos dados
        self.exported_data = {
            'export_info': export_info,
            'pages': pages_data
        }
    
    def _get_custom_fields(self, page):
        """Retorna os campos personalizados da página"""
        fields = {}
        
        for field_value in page.field_values.select_related('field__group').all():
            group_slug = field_value.field.group.slug
            field_slug = field_value.field.slug
            
            if group_slug not in fields:
                fields[group_slug] = {}
            
            # Processa o valor com base no tipo de campo
            if field_value.field.field_type in ['file', 'image', 'video', 'audio'] and field_value.file:
                fields[group_slug][field_slug] = {
                    'type': field_value.field.field_type,
                    'value': field_value.file.url,
                    'file_name': os.path.basename(field_value.file.name)
                }
            else:
                fields[group_slug][field_slug] = {
                    'type': field_value.field.field_type,
                    'value': field_value.value
                }
        
        return fields
    
    def _get_meta_items(self, page):
        """Retorna os metadados adicionais da página"""
        meta = {}
        
        for meta_item in page.meta_items.all():
            meta[meta_item.key] = meta_item.value
        
        return meta
    
    def _get_galleries(self, page):
        """Retorna as galerias da página"""
        galleries = []
        
        for gallery in page.galleries.all():
            gallery_data = {
                'name': gallery.name,
                'slug': gallery.slug,
                'description': gallery.description,
                'created_at': gallery.created_at.isoformat(),
                'images': []
            }
            
            # Imagens da galeria
            for image in gallery.images.all():
                image_data = {
                    'title': image.title,
                    'alt_text': image.alt_text,
                    'description': image.description,
                    'order': image.order,
                    'file_url': image.image.url,
                    'file_name': os.path.basename(image.image.name)
                }
                gallery_data['images'].append(image_data)
            
            galleries.append(gallery_data)
        
        return galleries
    
    def get_export_data(self):
        """Retorna os dados em formato JSON"""
        return json.dumps(self.exported_data, indent=2)


class XMLExporter(BaseExporter):
    """Exportador para formato XML"""
    
    def prepare_export(self):
        """Prepara os dados para exportação em XML"""
        # Usamos o serializador do Django para XML
        self.exported_data = serializers.serialize(
            'xml', 
            self.queryset,
            indent=2,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True
        )
        
        # Nota: O serializador padrão não exporta relações complexas,
        # seria necessário estender para um uso mais avançado


class CSVExporter(BaseExporter):
    """Exportador para formato CSV"""
    
    def prepare_export(self):
        """Prepara os dados para exportação em CSV"""
        output = StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        headers = [
            'ID', 'Title', 'Slug', 'Summary', 'Status', 
            'Created At', 'Updated At', 'Published At',
            'Template', 'Parent', 'Categories', 'Created By'
        ]
        writer.writerow(headers)
        
        # Linhas para cada página
        for page in self.queryset:
            row = [
                page.id,
                page.title,
                page.slug,
                page.summary,
                page.status,
                page.created_at.isoformat() if page.created_at else '',
                page.updated_at.isoformat() if page.updated_at else '',
                page.published_at.isoformat() if page.published_at else '',
                page.template.slug if page.template else '',
                page.parent.slug if page.parent else '',
                ','.join([cat.slug for cat in page.categories.all()]),
                page.created_by.username if page.created_by else ''
            ]
            writer.writerow(row)
        
        self.exported_data = output.getvalue()
        output.close()


class YAMLExporter(BaseExporter):
    """Exportador para formato YAML"""
    
    def prepare_export(self):
        """Prepara os dados para exportação em YAML"""
        # Similar ao JSON, mas formatado como YAML
        pages_data = []
        
        for page in self.queryset:
            # Dados básicos da página
            page_data = {
                'id': page.id,
                'title': page.title,
                'slug': page.slug,
                'content': page.content,
                'summary': page.summary,
                'status': page.status,
                'created_at': page.created_at.isoformat(),
                'updated_at': page.updated_at.isoformat(),
                'published_at': page.published_at.isoformat() if page.published_at else None,
                'meta_title': page.meta_title,
                'meta_description': page.meta_description,
                'meta_keywords': page.meta_keywords,
                'created_by': page.created_by.username if page.created_by else None,
                'template': page.template.slug if page.template else None,
                'parent': page.parent.slug if page.parent else None,
                'categories': [cat.slug for cat in page.categories.all()],
                'fields': self._get_custom_fields(page),
                'meta': self._get_meta_items(page),
            }
            
            pages_data.append(page_data)
        
        # Dados de exportação
        export_info = {
            'export_date': self.export_date.isoformat(),
            'exporter': self.user.username if self.user else 'anonymous',
            'version': '1.0',
            'count': len(pages_data)
        }
        
        # Montagem final dos dados
        export_data = {
            'export_info': export_info,
            'pages': pages_data
        }
        
        # Convertendo para YAML
        self.exported_data = yaml.dump(export_data, sort_keys=False, allow_unicode=True)
    
    def _get_custom_fields(self, page):
        """Retorna os campos personalizados da página"""
        fields = {}
        
        for field_value in page.field_values.select_related('field__group').all():
            group_slug = field_value.field.group.slug
            field_slug = field_value.field.slug
            
            if group_slug not in fields:
                fields[group_slug] = {}
            
            fields[group_slug][field_slug] = field_value.value
        
        return fields
    
    def _get_meta_items(self, page):
        """Retorna os metadados adicionais da página"""
        meta = {}
        
        for meta_item in page.meta_items.all():
            meta[meta_item.key] = meta_item.value
        
        return meta


class ZipExporter(BaseExporter):
    """Exportador para formato ZIP com JSON e arquivos"""
    
    def prepare_export(self):
        """Prepara os dados para exportação em ZIP"""
        # Cria um arquivo ZIP em memória
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Exporta os dados em JSON
            json_exporter = JSONExporter(self.queryset, self.user)
            json_data = json_exporter.export()
            
            # Adiciona o arquivo JSON ao ZIP
            zip_file.writestr('pages.json', json_data)
            
            # Adiciona os arquivos associados (imagens, mídia, etc.)
            self._add_files_to_zip(zip_file)
            
            # Adiciona um arquivo README
            readme_content = self._generate_readme()
            zip_file.writestr('README.txt', readme_content)
        
        # Obtém os dados do ZIP
        zip_buffer.seek(0)
        self.exported_data = zip_buffer.getvalue()
        zip_buffer.close()
    
    def _add_files_to_zip(self, zip_file):
        """Adiciona arquivos associados às páginas ao arquivo ZIP"""
        media_root = settings.MEDIA_ROOT
        media_url = settings.MEDIA_URL
        
        files_added = set()  # Para evitar duplicatas
        
        for page in self.queryset:
            # Adiciona a imagem OG, se existir
            if page.og_image:
                file_path = os.path.join(media_root, page.og_image.name)
                zip_path = os.path.join('media', page.og_image.name)
                
                if file_path not in files_added and os.path.exists(file_path):
                    zip_file.write(file_path, zip_path)
                    files_added.add(file_path)
            
            # Adiciona arquivos de campos personalizados
            for field_value in page.field_values.filter(file__isnull=False):
                if field_value.file:
                    file_path = os.path.join(media_root, field_value.file.name)
                    zip_path = os.path.join('media', field_value.file.name)
                    
                    if file_path not in files_added and os.path.exists(file_path):
                        zip_file.write(file_path, zip_path)
                        files_added.add(file_path)
            
            # Adiciona imagens de galerias
            for gallery in page.galleries.all():
                for image in gallery.images.all():
                    if image.image:
                        file_path = os.path.join(media_root, image.image.name)
                        zip_path = os.path.join('media', image.image.name)
                        
                        if file_path not in files_added and os.path.exists(file_path):
                            zip_file.write(file_path, zip_path)
                            files_added.add(file_path)
    
    def _generate_readme(self):
        """Gera um arquivo README com informações sobre a exportação"""
        readme = f"""EXPORTED CONTENT - README
        
        Export Date: {self.export_date.strftime('%Y-%m-%d %H:%M:%S')}
        Exported By: {self.user.username if self.user else 'Anonymous'}
        Pages Count: {self.queryset.count()}

        This archive contains the following files:
        - pages.json: Contains all page data in JSON format
        - media/: Directory with all associated files (images, documents, etc.)

        IMPORT INSTRUCTIONS:
        1. In the CMS admin panel, go to "Content" > "Import/Export"
        2. Choose "Import from ZIP"
        3. Upload this ZIP file
        4. Follow the instructions to map and import content

        Note: The import process will check for conflicts with existing content.
        You will have the option to skip, update, or create new versions of pages.

        For more information, refer to the documentation.
        """
        return readme