from django.contrib import admin
import admin_thumbnails
from .models import Service, Project

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    search_fields = ('name', 'description')

@admin_thumbnails.thumbnail('image')
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'service', 'completion_date', 'image_thumbnail')
    list_filter = ('service', 'completion_date')
    search_fields = ('title', 'description')

