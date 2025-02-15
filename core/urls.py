from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('apps.home.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('services/', include('apps.services.urls')),
    path('blog/', include('apps.blog.urls')),
    path('colors/', include('apps.colors.urls')),
    path('contact/', include('apps.contact.urls')),
    path('quotes/', include('apps.quotes.urls')),
    path('accounts/', include('apps.users.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)