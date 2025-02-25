# your_cms_app/pages/urls.py

from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    # URLs para visualização pública de páginas
    path('', views.PageListView.as_view(), name='page_list'),
    path('page/<slug:slug>/', views.PageDetailView.as_view(), name='page_detail'),
    path('pages/<path:path>/', views.PageDetailView.as_view(), name='page_path'),
    path('category/<slug:category_slug>/', views.PageListView.as_view(), name='page_category'),
    path('search/', views.PageSearchView.as_view(), name='page_search'),
    
    # URLs para gerenciamento de páginas
    path('admin/page/create/', views.PageCreateView.as_view(), name='page_create'),
    path('admin/page/<int:pk>/update/', views.PageUpdateView.as_view(), name='page_update'),
    path('admin/page/<int:pk>/delete/', views.PageDeleteView.as_view(), name='page_delete'),
    path('admin/page/<int:pk>/publish/', views.PagePublishView.as_view(), name='page_publish'),
    path('admin/page/<int:pk>/unpublish/', views.PageUnpublishView.as_view(), name='page_unpublish'),
    path('admin/page/<int:pk>/archive/', views.PageArchiveView.as_view(), name='page_archive'),
    path('admin/page/<int:pk>/request_review/', views.PagePublishView.as_view(), name='page_request_review'),
    path('admin/page/<int:pk>/preview/', views.page_preview, name='page_preview'),
    
    # URLs para gerenciamento de versões
    path('admin/page/<int:page_id>/version/<int:version_number>/', views.PageVersionDetailView.as_view(), name='page_version_detail'),
    path('admin/page/<int:page_id>/version/<int:version_id>/restore/', views.PageVersionRestoreView.as_view(), name='page_version_restore'),
    
    # URLs para gerenciamento de revisões
    path('admin/revision/<int:pk>/review/', views.PageRevisionReviewView.as_view(), name='page_revision_review'),
    
    # URLs para gerenciamento de galerias
    path('admin/page/<int:page_id>/gallery/create/', views.GalleryCreateView.as_view(), name='gallery_create'),
    path('admin/gallery/<int:pk>/update/', views.GalleryUpdateView.as_view(), name='gallery_update'),
    path('admin/gallery/<int:pk>/delete/', views.GalleryDeleteView.as_view(), name='gallery_delete'),
    path('admin/gallery/<int:gallery_id>/upload_image/', views.gallery_upload_image, name='gallery_upload_image'),
    path('admin/gallery/image/<int:image_id>/update/', views.gallery_update_image, name='gallery_update_image'),
    path('admin/gallery/image/<int:image_id>/delete/', views.gallery_delete_image, name='gallery_delete_image'),
    path('admin/gallery/<int:gallery_id>/reorder_images/', views.gallery_reorder_images, name='gallery_reorder_images'),
    
    # URLs para gerenciamento de notificações
    path('admin/notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('admin/notification/<int:notification_id>/mark_read/', views.mark_notification_as_read, name='mark_notification_read'),
    path('admin/notifications/mark_all_read/', views.mark_all_notifications_as_read, name='mark_all_notifications_read'),
    
    # URLs para APIs AJAX
    path('api/page/check_slug/', views.page_check_slug, name='page_check_slug'),
    path('api/page/<int:page_id>/add_comment/', views.page_add_comment, name='page_add_comment'),
    path('api/editor/pages/', views.editor_page_list, name='editor_page_list'),
    path('api/editor/images/', views.editor_image_list, name='editor_image_list'),
    
    # URLs para exportação e feeds
    path('export/page/<int:page_id>.<str:format>/', views.export_page, name='export_page'),
    path('sitemap.xml', views.PageSitemapView.as_view(), name='sitemap'),
    path('feed.xml', views.PageRSSFeedView.as_view(), name='rss_feed'),
    
    # URLs para templates
    path('admin/templates/', views.TemplateListView.as_view(), name='template_list'),
]