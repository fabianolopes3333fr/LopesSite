from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Rotas para o sistema de páginas
router.register(r'page-categories', views.PageCategoryViewSet)
router.register(r'page-templates', views.PageTemplateViewSet)
router.register(r'field-groups', views.FieldGroupViewSet)
router.register(r'field-definitions', views.FieldDefinitionViewSet)
router.register(r'pages', views.PageViewSet)
router.register(r'page-versions', views.PageVersionViewSet)
router.register(r'page-field-values', views.PageFieldValueViewSet)
router.register(r'page-galleries', views.PageGalleryViewSet)
router.register(r'page-images', views.PageImageViewSet)
router.register(r'page-comments', views.PageCommentViewSet)
router.register(r'page-metas', views.PageMetaViewSet)
router.register(r'page-redirects', views.PageRedirectViewSet)
router.register(r'page-revision-requests', views.PageRevisionRequestViewSet)
router.register(r'page-notifications', views.PageNotificationViewSet)

# Rotas para o sistema de templates
router.register(r'template-categories', views.TemplateCategoryViewSet)
router.register(r'template-types', views.TemplateTypeViewSet)
router.register(r'django-templates', views.DjangoTemplateViewSet)
router.register(r'component-templates', views.ComponentTemplateViewSet)
router.register(r'layout-templates', views.LayoutTemplateViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Ações personalizadas para páginas
    path('pages/<int:pk>/publish/', views.PageViewSet.as_view({'post': 'publish'}), name='page-publish'),
    path('pages/<int:pk>/unpublish/', views.PageViewSet.as_view({'post': 'unpublish'}), name='page-unpublish'),
    path('pages/<int:pk>/archive/', views.PageViewSet.as_view({'post': 'archive'}), name='page-archive'),
    path('pages/<int:pk>/check-slug/', views.PageViewSet.as_view({'get': 'check_slug'}), name='page-check-slug'),

    # Ações personalizadas para versões de página
    path('page-versions/<int:pk>/restore/', views.PageVersionViewSet.as_view({'post': 'restore'}), name='pageversion-restore'),

    # Ações personalizadas para galerias de página
    path('page-galleries/<int:pk>/reorder-images/', views.PageGalleryViewSet.as_view({'post': 'reorder_images'}), name='pagegallery-reorder-images'),

    # Ações personalizadas para solicitações de revisão
    path('page-revision-requests/<int:pk>/review/', views.PageRevisionRequestViewSet.as_view({'post': 'review'}), name='pagerevisionrequest-review'),
]