# your_cms_app/api/views.py
from rest_framework.permissions import IsAdminUser
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Q

from ..pages.models import (
    PageCategory, PageNotification, PageRedirect, PageTemplate, FieldGroup, FieldDefinition,
    Page, PageVersion, PageFieldValue, PageGallery, PageImage, 
    PageComment, PageMeta, PageRevisionRequest
)
from ..widgets.models import (
    TemplateCategory, TemplateType, DjangoTemplate, 
    ComponentTemplate, LayoutTemplate
)
from .serializers import (
    PageCategorySerializer, PageNotificationSerializer, PageTemplateSerializer, FieldGroupSerializer,
    FieldDefinitionSerializer, PageListSerializer, PageDetailSerializer,
    PageVersionSerializer, PageFieldValueSerializer, PageGallerySerializer,
    PageImageSerializer, PageCommentSerializer, PageMetaSerializer,
    TemplateCategorySerializer, TemplateTypeSerializer, DjangoTemplateSerializer,
    ComponentTemplateSerializer, LayoutTemplateSerializer, PageRedirectSerializer,
    PageRevisionRequestSerializer
    
)
from .permissions import (
    IsAdminOrReadOnly, IsOwnerOrReadOnly, CanPublishPage
)
from .filters import PageFilter


class PageCategoryViewSet(viewsets.ModelViewSet):
    """API endpoint para categorias de páginas"""
    queryset = PageCategory.objects.all()
    serializer_class = PageCategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'parent']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'order', 'created_at']
    ordering = ['order', 'name']


class PageTemplateViewSet(viewsets.ModelViewSet):
    """API endpoint para templates de páginas"""
    queryset = PageTemplate.objects.all()
    serializer_class = PageTemplateSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'layout']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']



class FieldGroupViewSet(viewsets.ModelViewSet):
    """API endpoint para grupos de campos"""
    queryset = FieldGroup.objects.all()
    serializer_class = FieldGroupSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['template']
    ordering_fields = ['order', 'name']
    ordering = ['template', 'order', 'name']


class FieldDefinitionViewSet(viewsets.ModelViewSet):
    """API endpoint para definições de campos"""
    queryset = FieldDefinition.objects.all()
    serializer_class = FieldDefinitionSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['group', 'field_type', 'is_required', 'is_searchable']
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name']
    ordering = ['group', 'order', 'name']
    
    
class PageViewSet(viewsets.ModelViewSet):
    """API endpoint para páginas"""
    queryset = Page.objects.all()
    
    
    
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PageFilter
    search_fields = ['title', 'summary', 'content', 'meta_keywords']
    ordering_fields = ['title', 'created_at', 'updated_at', 'published_at', 'order']
    ordering = ['-published_at', 'order', 'title']

    def get_queryset(self):
        """
        Filtra o queryset com base no usuário atual e parâmetros da requisição.
        """
        queryset = Page.objects.all()

        # Se não estiver autenticado, mostra apenas páginas publicadas públicas
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(
                status='published', 
                visibility='public',
                published_at__lte=timezone.now()
            )
        # Se estiver autenticado mas não for staff, mostra publicadas e próprias
        elif not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(status='published', visibility='public', published_at__lte=timezone.now()) |
                Q(created_by=self.request.user)
            )

        # Filtra por categoria, se especificada
        category = self.request.query_params.get('category', None)
        if category is not None:
            queryset = queryset.filter(categories__slug=category)

        # Filtra por página pai, se especificada
        parent = self.request.query_params.get('parent', None)
        if parent is not None:
            if parent == 'root':
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent__slug=parent)

        return queryset

    def get_serializer_class(self):
        """
        Retorna serializador diferente com base na ação.
        """
        if self.action == 'list':
            return PageListSerializer
        return PageDetailSerializer

    def perform_create(self, serializer):
        """Adiciona o usuário atual como criador da página"""
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        """Atualiza o usuário que modificou a página"""
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, CanPublishPage])
    def publish(self, request, pk=None):
        """Ação para publicar uma página"""
        page = self.get_object()

        if page.status == 'published':
            return Response(
                {'detail': 'A página já está publicada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Atualiza o status da página para publicado
        page.status = 'published'
        page.published_at = timezone.now()
        page.published_by = request.user
        page.save(update_fields=['status', 'published_at', 'published_by'])

        # Cria uma versão com o status publicado
        comment = request.data.get('comment', '')
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
            status='published',
            meta_title=page.meta_title,
            meta_description=page.meta_description,
            meta_keywords=page.meta_keywords,
            comment=comment or f"Página publicada por {request.user.get_full_name() or request.user.username}"
        )

        serializer = self.get_serializer(page)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, CanPublishPage])
    def unpublish(self, request, pk=None):
        """Ação para despublicar uma página"""
        page = self.get_object()

        if page.status != 'published':
            return Response(
                {'detail': 'A página não está publicada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Atualiza o status da página para rascunho
        page.status = 'draft'
        page.save(update_fields=['status'])

        # Cria uma versão com o status rascunho
        comment = request.data.get('comment', '')
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
            comment=comment or f"Página despublicada por {request.user.get_full_name() or request.user.username}"
        )

        serializer = self.get_serializer(page)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        page = self.get_object()
        page.archive()
        return Response({'status': 'page archived'})

    @action(detail=False, methods=['get'])
    def check_slug(self, request):
        slug = request.query_params.get('slug', None)
        if slug is None:
            return Response({'error': 'No slug provided'}, status=status.HTTP_400_BAD_REQUEST)
        exists = Page.objects.filter(slug=slug).exists()
        return Response({'slug_exists': exists})

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Retorna as versões de uma página"""
        page = self.get_object()
        versions = page.versions.order_by('-version_number')
        serializer = PageVersionSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Retorna os comentários de uma página"""
        page = self.get_object()

        if not page.enable_comments:
            return Response([])

        # Filtra apenas comentários aprovados
        comments = page.comments.filter(is_approved=True)

        # Se for usuário staff, mostra também os não aprovados
        if request.user.is_staff:
            comments = page.comments.all()

        serializer = PageCommentSerializer(comments, many=True)
        return Response(serializer.data)
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Adiciona um comentário a uma página"""
        page = self.get_object()

        if not page.enable_comments:
            return Response(
                {'detail': 'Os comentários estão desativados para esta página.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cria o serializador com os dados do comentário
        serializer = PageCommentSerializer(data=request.data)

        if serializer.is_valid():
            # Configura os campos adicionais
            comment = serializer.save(
                page=page,
                is_approved=request.user.is_staff,  # Aprovação automática para staff
                user=request.user if request.user.is_authenticated else None
            )

            # Retorna o comentário criado
            return Response(
                PageCommentSerializer(comment).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def restore_version(self, request, pk=None):
        """Restaura uma versão específica da página"""
        page = self.get_object()
        version_id = request.data.get('version_id')

        if not version_id:
            return Response(
                {'detail': 'ID da versão não fornecido.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            version = PageVersion.objects.get(id=version_id, page=page)
        except PageVersion.DoesNotExist:
            return Response(
                {'detail': 'Versão não encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Restaura a versão
        version.restore()

        # Atualiza o usuário que fez a restauração
        page.updated_by = request.user
        page.save(update_fields=['updated_by'])

        return Response({'detail': f'Versão {version.version_number} restaurada com sucesso.'})


class PageVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint para versões de páginas"""
    queryset = PageVersion.objects.all()
    serializer_class = PageVersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['page', 'status', 'created_by']
    ordering_fields = ['version_number', 'created_at']
    ordering = ['-version_number']
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        version = self.get_object()
        version.restore()
        return Response({'status': 'version restored'})
    
    
class PageFieldValueViewSet(viewsets.ModelViewSet):
    """API endpoint para valores de campos de páginas"""
    queryset = PageFieldValue.objects.all()
    serializer_class = PageFieldValueSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['page', 'field']

class PageGalleryViewSet(viewsets.ModelViewSet):
    """API endpoint para galerias de páginas"""
    queryset = PageGallery.objects.all()
    serializer_class = PageGallerySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['page']
    search_fields = ['name']
    
    @action(detail=True, methods=['post'])
    def reorder_images(self, request, pk=None):
        gallery = self.get_object()
        image_ids = request.data.get('image_ids', [])
        for index, image_id in enumerate(image_ids):
            image = get_object_or_404(PageImage, id=image_id, gallery=gallery)
            image.order = index
            image.save()
        return Response({'status': 'images reordered'})

class PageImageViewSet(viewsets.ModelViewSet):
    """API endpoint para imagens de páginas"""
    queryset = PageImage.objects.all()
    serializer_class = PageImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['gallery']
    ordering_fields = ['order']
    ordering = ['order']

class PageCommentViewSet(viewsets.ModelViewSet):
    """API endpoint para comentários de páginas"""
    queryset = PageComment.objects.all()
    serializer_class = PageCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['page', 'is_approved', 'created_by']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        
        
class PageMetaViewSet(viewsets.ModelViewSet):
    """API endpoint para metadados de páginas"""
    queryset = PageMeta.objects.all()
    serializer_class = PageMetaSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['page']


    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def dislike(self, request, pk=None):
        """Adiciona não curtida a um comentário"""
        comment = self.get_object()

        # Aumenta o contador de não curtidas
        comment.dislikes += 1
        comment.save(update_fields=['dislikes'])

        return Response({'likes': comment.likes, 'dislikes': comment.dislikes})

class PageRedirectViewSet(viewsets.ModelViewSet):
    """API endpoint para redirecionamentos de páginas"""
    queryset = PageRedirect.objects.all()
    serializer_class = PageRedirectSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['old_path', 'new_path', 'is_permanent']
    search_fields = ['old_path', 'new_path']

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Cria múltiplos redirecionamentos de uma vez"""
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'])
    def check_redirect(self, request):
        """Verifica se existe um redirecionamento para um determinado caminho"""
        path = request.query_params.get('path', None)
        if path is None:
            return Response({'error': 'Path parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        redirect = PageRedirect.objects.filter(old_path=path).first()
        if redirect:
            return Response({
                'exists': True,
                'old_path': redirect.old_path,
                'new_path': redirect.new_path,
                'is_permanent': redirect.is_permanent
            })
        return Response({'exists': False})
    
class PageRevisionRequestViewSet(viewsets.ModelViewSet):
    """API endpoint para solicitações de revisão de páginas"""
    queryset = PageRevisionRequest.objects.all()
    serializer_class = PageRevisionRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'page', 'requested_by', 'reviewer']
    search_fields = ['page__title', 'comment', 'reviewer_comment']
    ordering_fields = ['requested_at', 'updated_at', 'completed_at']
    ordering = ['-requested_at']

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def approve(self, request, pk=None):
        revision_request = self.get_object()
        comment = request.data.get('comment', '')
        revision_request.approve(reviewer=request.user, comment=comment)
        serializer = self.get_serializer(revision_request)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        revision_request = self.get_object()
        comment = request.data.get('comment', '')
        revision_request.reject(reviewer=request.user, comment=comment)
        serializer = self.get_serializer(revision_request)
        return Response(serializer.data)

class PageNotificationViewSet(viewsets.ModelViewSet):
    queryset = PageNotification.objects.all()
    serializer_class = PageNotificationSerializer

class TemplateCategoryViewSet(viewsets.ModelViewSet):
    """API endpoint para categorias de templates"""
    queryset = TemplateCategory.objects.all()
    serializer_class = TemplateCategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'order']
    ordering = ['order', 'name']

class TemplateTypeViewSet(viewsets.ModelViewSet):
    """API endpoint para tipos de templates"""
    queryset = TemplateType.objects.all()
    serializer_class = TemplateTypeSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name']
    ordering_fields = ['name', 'order']
    ordering = ['order', 'name']

class DjangoTemplateViewSet(viewsets.ModelViewSet):
    """API endpoint para templates Django"""
    queryset = DjangoTemplate.objects.all()
    serializer_class = DjangoTemplateSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class ComponentTemplateViewSet(viewsets.ModelViewSet):
    """API endpoint para templates de componentes"""
    queryset = ComponentTemplate.objects.all()
    serializer_class = ComponentTemplateSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class LayoutTemplateViewSet(viewsets.ModelViewSet):
    """API endpoint para templates de layout"""
    queryset = LayoutTemplate.objects.all()
    serializer_class = LayoutTemplateSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

