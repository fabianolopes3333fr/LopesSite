import django_filters
from ..pages.models import Page
from django.db.models import Q


class PageFilter(django_filters.FilterSet):
    """Filtros personalizados para o modelo Page"""
    
    # Filtra por título ou conteúdo
    search = django_filters.CharFilter(method='filter_search')
    
    # Filtra por categoria
    category = django_filters.CharFilter(field_name='categories__slug')
    
    # Filtra por status
    status = django_filters.CharFilter(field_name='status')
    
    # Filtra por visibilidade
    visibility = django_filters.CharFilter(field_name='visibility')
    
    # Filtra por template
    template = django_filters.CharFilter(field_name='template__slug')
    
    # Filtra por autor
    author = django_filters.CharFilter(field_name='created_by__username')
    
    # Filtra por data de publicação
    published_from = django_filters.DateFilter(field_name='published_at', lookup_expr='gte')
    published_to = django_filters.DateFilter(field_name='published_at', lookup_expr='lte')
    
    # Filtra por data de criação
    created_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    # Filtra por página pai
    parent = django_filters.CharFilter(field_name='parent__slug')

    # Filtra por nível na hierarquia
    level = django_filters.NumberFilter(field_name='level')

    # Filtra por páginas que são folhas (não têm filhos)
    is_leaf = django_filters.BooleanFilter(field_name='is_leaf_node')
    
    # Filtra por tags
    tags = django_filters.CharFilter(field_name='tags__slug', lookup_expr='in')
    
    # Filtra por campos personalizados
    custom_field = django_filters.CharFilter(method='filter_custom_field')
    
    # Ordenação
    ordering = django_filters.OrderingFilter(
        fields=(
            ('title', 'title'),
            ('created_at', 'created_at'),
            ('published_at', 'published_at'),
            ('order', 'order'),
        ),
    )
    
    class Meta:
        model = Page
        fields = [
            'search', 'category', 'status', 'visibility', 'template',
            'author', 'published_from', 'published_to', 'created_from',
            'created_to', 'is_indexable', 'is_visible_in_menu', 'parent',
            'level', 'is_leaf', 'tags', 'custom_field', 'ordering'
        ]
    
    def filter_custom_field(self, queryset, name, value):
        """
        Filtra por campos personalizados.
        Formato esperado: 'nome_do_campo:valor'
        """
        if ':' in value:
            field, val = value.split(':', 1)
            return queryset.filter(custom_fields__name=field, custom_fields__value__icontains=val)
        return queryset
    
    def filter_search(self, queryset, name, value):
        """
        Filtra por título, conteúdo ou resumo.
        """
        return queryset.filter(
            Q(title__icontains=value) |
            Q(content__icontains=value) |
            Q(summary__icontains=value) |
            Q(meta_keywords__icontains=value) |
            Q(slug__icontains=value)
        )