from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('services/', include('services.urls')),
    path('blog/', include('blog.urls')),
    path('colors/', include('colors.urls')),
    path('contact/', include('contact.urls')),
    path('quotes/', include('quotes.urls')),
    path('users/', include('apps.users.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)