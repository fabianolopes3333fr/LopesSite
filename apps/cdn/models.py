# your_cms_app/cdn/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.files.storage import Storage, FileSystemStorage
from django.utils.deconstruct import deconstructible
import os
import boto3
import hashlib
import time
import mimetypes
import requests
from urllib.parse import urljoin, urlparse


class CDNProvider(models.Model):
    """
    Modelo para armazenar configurações de provedores CDN
    """
    PROVIDER_TYPES = (
        ('s3', 'Amazon S3'),
        ('cloudfront', 'Amazon CloudFront'),
        ('cloudflare', 'Cloudflare'),
        ('bunny', 'Bunny.net'),
        ('custom', 'Custom CDN')
    )
    
    name = models.CharField(_('Nome'), max_length=100)
    provider_type = models.CharField(_('Tipo de Provedor'), max_length=20, choices=PROVIDER_TYPES)
    base_url = models.URLField(_('URL Base'), max_length=255, 
                            help_text=_('URL base do CDN (ex: https://cdn.example.com/)'))
    is_active = models.BooleanField(_('Ativo'), default=True)
    
    # Configurações para Amazon S3 / CloudFront
    s3_bucket_name = models.CharField(_('Nome do Bucket S3'), max_length=255, blank=True)
    s3_region = models.CharField(_('Região S3'), max_length=50, blank=True)
    s3_access_key = models.CharField(_('Access Key ID'), max_length=255, blank=True)
    s3_secret_key = models.CharField(_('Secret Access Key'), max_length=255, blank=True)
    
    # Configurações para Cloudflare
    cloudflare_account_id = models.CharField(_('ID da Conta Cloudflare'), max_length=255, blank=True)
    cloudflare_api_token = models.CharField(_('Token API Cloudflare'), max_length=255, blank=True)
    
    # Configurações para Bunny.net
    bunny_storage_zone = models.CharField(_('Zona de Armazenamento Bunny.net'), max_length=255, blank=True)
    bunny_api_key = models.CharField(_('Chave API Bunny.net'), max_length=255, blank=True)
    
    # Configurações personalizadas
    custom_headers = models.TextField(_('Cabeçalhos HTTP Personalizados'), blank=True,
                                   help_text=_('Cabeçalhos HTTP para enviar com as requisições, um por linha (nome: valor)'))
    
    # Configurações avançadas
    invalidation_url = models.URLField(_('URL de Invalidação'), max_length=255, blank=True,
                                    help_text=_('URL para API de invalidação de cache'))
    use_signed_urls = models.BooleanField(_('Usar URLs Assinadas'), default=False,
                                      help_text=_('Gerar URLs assinadas para acesso seguro aos arquivos'))
    
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Provedor CDN')
        verbose_name_plural = _('Provedores CDN')
    
    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"
    
    def get_client(self):
        """
        Retorna um cliente para o provedor CDN
        """
        if self.provider_type == 's3' or self.provider_type == 'cloudfront':
            # Retorna cliente S3
            return boto3.client(
                's3',
                aws_access_key_id=self.s3_access_key,
                aws_secret_access_key=self.s3_secret_key,
                region_name=self.s3_region
            )
        elif self.provider_type == 'cloudflare':
            # Inicializa o cliente Cloudflare (seria necessário uma biblioteca adicional)
            return None
        elif self.provider_type == 'bunny':
            # Inicializa o cliente Bunny.net (seria necessário uma biblioteca adicional)
            return None
        else:
            # Para CDN personalizado, retorna None
            return None
    
    def get_storage(self):
        """
        Retorna um objeto Storage para este provedor CDN
        """
        if self.provider_type == 's3' or self.provider_type == 'cloudfront':
            return S3Storage(
                bucket_name=self.s3_bucket_name,
                access_key=self.s3_access_key,
                secret_key=self.s3_secret_key,
                region=self.s3_region,
                base_url=self.base_url if self.provider_type == 'cloudfront' else None
            )
        elif self.provider_type == 'custom':
            return CDNProxyStorage(
                base_url=self.base_url,
                local_storage=FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)
            )
        else:
            # Se não tiver implementação específica, usa o armazenamento padrão
            return FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)
    
    def invalidate_cache(self, paths):
        """
        Invalida o cache para os caminhos fornecidos
        """
        if not paths:
            return False
            
        if self.provider_type == 'cloudfront':
            # Invalidação CloudFront
            try:
                cloudfront = boto3.client(
                    'cloudfront',
                    aws_access_key_id=self.s3_access_key,
                    aws_secret_access_key=self.s3_secret_key,
                    region_name=self.s3_region
                )
                
                # Obtém o ID da distribuição CloudFront
                distribution_id = self.base_url.split('.')[-3]  # Método simples para extrair o ID
                
                # Cria a solicitação de invalidação
                response = cloudfront.create_invalidation(
                    DistributionId=distribution_id,
                    InvalidationBatch={
                        'Paths': {
                            'Quantity': len(paths),
                            'Items': paths
                        },
                        'CallerReference': str(int(time.time()))
                    }
                )
                
                return True
            except Exception as e:
                print(f"Erro ao invalidar cache CloudFront: {str(e)}")
                return False
        
        elif self.provider_type == 'cloudflare' and self.invalidation_url:
            # Invalidação Cloudflare
            try:
                headers = {
                    'Authorization': f'Bearer {self.cloudflare_api_token}',
                    'Content-Type': 'application/json'
                }
                data = {
                    'files': paths
                }
                response = requests.post(self.invalidation_url, headers=headers, json=data)
                return response.status_code == 200
            except Exception as e:
                print(f"Erro ao invalidar cache Cloudflare: {str(e)}")
                return False
        
        elif self.provider_type == 'bunny' and self.invalidation_url:
            # Invalidação Bunny.net
            try:
                headers = {
                    'AccessKey': self.bunny_api_key,
                    'Content-Type': 'application/json'
                }
                data = {
                    'paths': paths
                }
                response = requests.post(self.invalidation_url, headers=headers, json=data)
                return response.status_code == 200
            except Exception as e:
                print(f"Erro ao invalidar cache Bunny.net: {str(e)}")
                return False
        
        elif self.provider_type == 'custom' and self.invalidation_url:
            # Invalidação personalizada
            try:
                headers = {}
                if self.custom_headers:
                    for line in self.custom_headers.split('\n'):
                        key, value = line.split(':', 1)
                        headers[key.strip()] = value.strip()
                
                data = {
                    'paths': paths
                }
                response = requests.post(self.invalidation_url, headers=headers, json=data)
                return response.status_code == 200
            except Exception as e:
                print(f"Erro ao invalidar cache personalizado: {str(e)}")
                return False
        
        return False


@deconstructible
class S3Storage(Storage):
    """
    Storage personalizado para Amazon S3
    """
    def __init__(self, bucket_name, access_key, secret_key, region, base_url=None):
        self.bucket_name = bucket_name
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.base_url = base_url
        self.client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

    def _open(self, name, mode='rb'):
        # Implementação para abrir um arquivo
        pass

    def _save(self, name, content):
        # Implementação para salvar um arquivo
        pass

    def delete(self, name):
        # Implementação para deletar um arquivo
        pass

    def exists(self, name):
        # Implementação para verificar se um arquivo existe
        pass

    def listdir(self, path):
        # Implementação para listar diretórios
        pass

    def size(self, name):
        # Implementação para obter o tamanho do arquivo
        pass

    def url(self, name):
        # Implementação para gerar a URL do arquivo
        if self.base_url:
            return urljoin(self.base_url, name)
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': name},
            ExpiresIn=3600
        )


@deconstructible
class CDNProxyStorage(Storage):
    """
    Storage que atua como proxy para um CDN personalizado
    """
    def __init__(self, base_url, local_storage):
        self.base_url = base_url
        self.local_storage = local_storage

    def _open(self, name, mode='rb'):
        return self.local_storage._open(name, mode)

    def _save(self, name, content):
        return self.local_storage._save(name, content)

    def delete(self, name):
        return self.local_storage.delete(name)

    def exists(self, name):
        return self.local_storage.exists(name)

    def listdir(self, path):
        return self.local_storage.listdir(path)

    def size(self, name):
        return self.local_storage.size(name)

    def url(self, name):
        return urljoin(self.base_url, name)


class CDNFile(models.Model):
    """
    Modelo para representar arquivos armazenados no CDN
    """
    provider = models.ForeignKey(CDNProvider, on_delete=models.CASCADE, verbose_name=_('Provedor CDN'))
    file = models.FileField(_('Arquivo'), upload_to='cdn_files/')
    original_filename = models.CharField(_('Nome original do arquivo'), max_length=255)
    content_type = models.CharField(_('Tipo de conteúdo'), max_length=100)
    file_size = models.PositiveIntegerField(_('Tamanho do arquivo'))
    file_hash = models.CharField(_('Hash do arquivo'), max_length=64)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('Arquivo CDN')
        verbose_name_plural = _('Arquivos CDN')

    def __str__(self):
        return self.original_filename

    def save(self, *args, **kwargs):
        if not self.pk:  # Se é um novo arquivo
            self.file_size = self.file.size
            self.content_type = mimetypes.guess_type(self.file.name)[0] or 'application/octet-stream'
            self.file_hash = self.calculate_hash()
        super().save(*args, **kwargs)

    def calculate_hash(self):
        """Calcula o hash SHA-256 do arquivo"""
        hasher = hashlib.sha256()
        for chunk in self.file.chunks():
            hasher.update(chunk)
        return hasher.hexdigest()

    def get_absolute_url(self):
        """Retorna a URL absoluta do arquivo no CDN"""
        return self.provider.get_storage().url(self.file.name)