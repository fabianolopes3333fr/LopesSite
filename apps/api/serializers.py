# your_cms_app/api/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from ..pages.models import (
    PageCategory, PageNotification, PageRevisionRequest, PageTemplate, FieldGroup, FieldDefinition, 
    Page, PageVersion, PageFieldValue, PageGallery, PageImage, 
    PageComment, PageMeta, PageRedirect
)
from ..widgets.models import (
    TemplateCategory, TemplateType, DjangoTemplate, 
    ComponentTemplate, LayoutTemplate
)


class UserSerializer(serializers.ModelSerializer):
    """Serializador para o modelo User"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_staff']


class PageCategorySerializer(serializers.ModelSerializer):
    """Serializador para o modelo PageCategory"""
    
    class Meta:
        model = PageCategory
        fields = ['id', 'name', 'slug', 'description', 'parent', 'icon', 
                  'color', 'is_active', 'order', 'created_at', 'updated_at']


class PageTemplateSerializer(serializers.ModelSerializer):
    """Serializador para o modelo PageTemplate"""
    
    class Meta:
        model = PageTemplate
        fields = ['id', 'name', 'slug', 'description', 'layout', 
                  'template_file', 'is_active', 'created_at', 'updated_at']


class FieldGroupSerializer(serializers.ModelSerializer):
    """Serializador para o modelo FieldGroup"""
    
    class Meta:
        model = FieldGroup
        fields = ['id', 'name', 'slug', 'description', 'template', 
                  'order', 'is_collapsible', 'is_collapsed']


class FieldDefinitionSerializer(serializers.ModelSerializer):
    """Serializador para o modelo FieldDefinition"""
    
    class Meta:
        model = FieldDefinition
        fields = ['id', 'name', 'slug', 'description', 'help_text', 
                  'field_type', 'default_value', 'placeholder', 
                  'is_required', 'min_length', 'max_length', 
                  'min_value', 'max_value', 'options', 
                  'validation_regex', 'allowed_extensions', 
                  'max_file_size', 'group', 'order', 'css_classes', 
                  'is_searchable', 'is_filterable', 'is_translatable']


class PageFieldValueSerializer(serializers.ModelSerializer):
    """Serializador para o modelo PageFieldValue"""
    
    class Meta:
        model = PageFieldValue
        fields = ['id', 'page', 'field', 'value', 'file', 
                  'content_type', 'object_id']


class PageCommentSerializer(serializers.ModelSerializer):
    """Serializador para o modelo PageComment"""
    
    class Meta:
        model = PageComment
        fields = ['id', 'page', 'parent', 'author_name', 'author_email', 
                  'author_url', 'user', 'comment', 'created_at', 
                  'updated_at', 'is_approved', 'likes', 'dislikes', 
                  'is_pinned']
        read_only_fields = ['is_approved', 'likes', 'dislikes', 'is_pinned']


class PageImageSerializer(serializers.ModelSerializer):
    """Serializador para o modelo PageImage"""
    
    class Meta:
        model = PageImage
        fields = ['id', 'gallery', 'image', 'title', 'alt_text', 
                  'description', 'order', 'created_at', 
                  'width', 'height', 'file_size']


class PageGallerySerializer(serializers.ModelSerializer):
    """Serializador para o modelo PageGallery"""
    images = PageImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = PageGallery
        fields = ['id', 'name', 'slug', 'description', 'page', 
                  'created_at', 'updated_at', 'created_by', 'images']


class PageMetaSerializer(serializers.ModelSerializer):
    """Serializador para o modelo PageMeta"""
    
    class Meta:
        model = PageMeta
        fields = ['id', 'page', 'key', 'value']


class PageVersionSerializer(serializers.ModelSerializer):
    """Serializador para o modelo PageVersion"""
    
    class Meta:
        model = PageVersion
        fields = ['id', 'page', 'title', 'content', 'summary', 
                  'version_number', 'created_at', 'created_by', 
                  'comment', 'custom_fields', 'status', 
                  'meta_title', 'meta_description', 'meta_keywords']


class PageListSerializer(serializers.ModelSerializer):
    """Serializador simplificado para listar páginas"""
    categories = PageCategorySerializer(many=True, read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    author_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Page
        fields = ['id', 'title', 'slug', 'summary', 'status', 
                  'published_at', 'categories', 'template_name', 
                  'is_indexable', 'is_visible_in_menu', 'author_name']
    
    def get_author_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class PageDetailSerializer(serializers.ModelSerializer):
    """Serializador detalhado para uma página individual"""
    categories = PageCategorySerializer(many=True, read_only=True)
    template = PageTemplateSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    published_by = UserSerializer(read_only=True)
    field_values = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    galleries = PageGallerySerializer(many=True, read_only=True)
    meta_items = PageMetaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Page
        fields = ['id', 'title', 'slug', 'content', 'summary', 
                  'parent', 'categories', 'template', 'status', 
                  'is_indexable', 'is_searchable', 'is_visible_in_menu', 
                  'visibility', 'created_at', 'updated_at', 
                  'published_at', 'scheduled_at', 'meta_title', 
                  'meta_description', 'meta_keywords', 'og_title', 
                  'og_description', 'og_image', 'og_type', 
                  'schema_type', 'schema_data', 'permalink', 
                  'enable_comments', 'enable_analytics', 'order', 
                  'created_by', 'updated_by', 'published_by', 
                  'field_values', 'comments', 'galleries', 'meta_items']
    
    def get_field_values(self, obj):
        """Retorna os valores dos campos personalizados formatados"""
        result = []
        for field_value in obj.field_values.select_related('field__group').all():
            result.append({
                'id': field_value.id,
                'field_id': field_value.field.id,
                'field_name': field_value.field.name,
                'field_slug': field_value.field.slug,
                'field_type': field_value.field.field_type,
                'group_name': field_value.field.group.name,
                'group_slug': field_value.field.group.slug,
                'value': field_value.value,
                'file_url': field_value.file.url if field_value.file else None,
                'display_value': field_value.get_value_display()
            })
        return result
    
    def get_comments(self, obj):
        """Retorna apenas comentários aprovados"""
        if not obj.enable_comments:
            return []
        
        comments = obj.comments.filter(is_approved=True, parent=None).order_by('-created_at')
        serializer = PageCommentSerializer(comments, many=True)
        return serializer.data


class TemplateCategorySerializer(serializers.ModelSerializer):
    """Serializador para o modelo TemplateCategory"""
    
    class Meta:
        model = TemplateCategory
        fields = ['id', 'name', 'slug', 'description', 'parent', 
                  'icon', 'color', 'is_active', 'order', 
                  'created_at', 'updated_at']


class TemplateTypeSerializer(serializers.ModelSerializer):
    """Serializador para o modelo TemplateType"""
    
    class Meta:
        model = TemplateType
        fields = ['id', 'name', 'slug', 'description', 'type', 
                  'category', 'icon', 'is_active', 'created_at', 'updated_at']


class DjangoTemplateSerializer(serializers.ModelSerializer):
    """Serializador para o modelo DjangoTemplate"""
    
    class Meta:
        model = DjangoTemplate
        fields = ['id', 'name', 'slug', 'description', 'file_path', 
                  'type', 'default_context', 'preview_image', 
                  'is_active', 'created_at', 'updated_at']


class ComponentTemplateSerializer(serializers.ModelSerializer):
    """Serializador para o modelo ComponentTemplate"""
    
    class Meta:
        model = ComponentTemplate
        fields = ['id', 'name', 'slug', 'description', 'component_type', 
                  'template_code', 'css_code', 'js_code', 'default_context', 
                  'icon', 'thumbnail', 'category', 'is_active', 
                  'created_at', 'updated_at']


class LayoutTemplateSerializer(serializers.ModelSerializer):
    """Serializador para o modelo LayoutTemplate"""
    
    class Meta:
        model = LayoutTemplate
        fields = ['id', 'name', 'slug', 'description', 'template', 
                  'header', 'footer', 'sidebar', 'thumbnail', 
                  'css_classes', 'is_default', 'is_active', 
                  'created_at', 'updated_at']
        
class PageExportSerializer(serializers.ModelSerializer):
    """Serializador para exportação de páginas"""
    categories = serializers.SlugRelatedField(many=True, read_only=True, slug_field='slug')
    template = serializers.SlugRelatedField(read_only=True, slug_field='slug')
    field_values = serializers.SerializerMethodField()
    galleries = serializers.SerializerMethodField()
    meta_items = PageMetaSerializer(many=True)

    class Meta:
        model = Page
        fields = '__all__'

    def get_field_values(self, obj):
        return {fv.field.slug: fv.value for fv in obj.field_values.all()}

    def get_galleries(self, obj):
        return [
            {
                'name': gallery.name,
                'slug': gallery.slug,
                'images': [
                    {
                        'image': image.image.url,
                        'title': image.title,
                        'alt_text': image.alt_text,
                        'order': image.order
                    } for image in gallery.images.all()
                ]
            } for gallery in obj.galleries.all()
        ]

class PageImportSerializer(serializers.ModelSerializer):
    """Serializador para importação de páginas"""
    categories = serializers.SlugRelatedField(many=True, queryset=PageCategory.objects.all(), slug_field='slug')
    template = serializers.SlugRelatedField(queryset=PageTemplate.objects.all(), slug_field='slug')
    field_values = serializers.DictField(child=serializers.CharField(), write_only=True)
    galleries = serializers.ListField(child=serializers.DictField(), write_only=True)
    meta_items = PageMetaSerializer(many=True)

    class Meta:
        model = Page
        fields = '__all__'

    def create(self, validated_data):
        field_values = validated_data.pop('field_values', {})
        galleries = validated_data.pop('galleries', [])
        meta_items = validated_data.pop('meta_items', [])

        page = super().create(validated_data)

        for field_slug, value in field_values.items():
            field = FieldDefinition.objects.get(slug=field_slug)
            PageFieldValue.objects.create(page=page, field=field, value=value)

        for gallery_data in galleries:
            gallery = PageGallery.objects.create(page=page, name=gallery_data['name'], slug=gallery_data['slug'])
            for image_data in gallery_data['images']:
                PageImage.objects.create(gallery=gallery, **image_data)

        for meta_item in meta_items:
            PageMeta.objects.create(page=page, **meta_item)

        return page
    
class PageRedirectSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageRedirect
        fields = ['id', 'old_path', 'new_path', 'is_permanent', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        
class PageRevisionRequestSerializer(serializers.ModelSerializer):
    """Serializador para o modelo PageRevisionRequest"""
    
    class Meta:
        model = PageRevisionRequest
        fields = ['id', 'page', 'requested_by', 'reviewer', 'comment', 
                  'status', 'requested_at', 'updated_at', 'completed_at', 
                  'reviewer_comment', 'version']
        read_only_fields = ['id', 'requested_at', 'updated_at', 'completed_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['page'] = instance.page.title
        representation['requested_by'] = instance.requested_by.get_full_name() or instance.requested_by.username
        if instance.reviewer:
            representation['reviewer'] = instance.reviewer.get_full_name() or instance.reviewer.username
        representation['status'] = instance.get_status_display()
        if instance.version:
            representation['version'] = instance.version.version_number
        return representation
class PageNotificationSerializer(serializers.ModelSerializer):
    """Serializador para o modelo PageNotification"""
    
    class Meta:
        model = PageNotification
        fields = ['id', 'notification_type', 'user', 'page', 'actor', 
                  'message', 'created_at', 'is_read', 'read_at', 'extra_data']
        read_only_fields = ['id', 'created_at', 'read_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['notification_type'] = instance.get_notification_type_display()
        representation['user'] = instance.user.get_full_name() or instance.user.username
        representation['page'] = instance.page.title
        if instance.actor:
            representation['actor'] = instance.actor.get_full_name() or instance.actor.username
        return representation
