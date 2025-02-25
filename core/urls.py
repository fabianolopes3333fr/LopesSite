from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('apps.home.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('services/', include('apps.services.urls')),
    path('inspiration/', include('apps.blog.urls')),
    path('colors/', include('apps.colors.urls')),
    path('contact/', include('apps.contact.urls')),
    path('quotes/', include('apps.quotes.urls')),
    path('accounts/', include('apps.users.urls')),
    path('config/', include('apps.config.urls')),
    path('pages/', include('apps.pages.urls')),
    path('widgets/', include('apps.widgets.urls')),
    
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)