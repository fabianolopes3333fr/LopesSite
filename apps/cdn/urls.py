from django.urls import path
from . import views

app_name = 'cdn'

urlpatterns = [
    # CDN Provider URLs
    path('providers/', views.cdn_provider_list, name='provider_list'),
    path('providers/create/', views.cdn_provider_create, name='provider_create'),
    path('providers/<int:pk>/', views.cdn_provider_detail, name='provider_detail'),
    path('providers/<int:pk>/update/', views.cdn_provider_update, name='provider_update'),
    path('providers/<int:pk>/delete/', views.cdn_provider_delete, name='provider_delete'),
    path('providers/<int:pk>/invalidate-cache/', views.invalidate_cache, name='invalidate_cache'),

    # CDN File URLs
    path('files/', views.cdn_file_list, name='file_list'),
    path('files/upload/', views.cdn_file_upload, name='file_upload'),
    path('files/<int:pk>/', views.cdn_file_detail, name='file_detail'),
    path('files/<int:pk>/delete/', views.cdn_file_delete, name='file_delete'),
    path('files/<int:pk>/url/', views.cdn_file_url, name='file_url'),
]