# your_cms_app/templates/urls.py

from django.urls import path
from . import views

app_name = 'templates'

urlpatterns = [
    # URLs para visualização e gerenciamento de templates
    path('templates/', views.TemplateListView.as_view(), name='template_list'),
    path('templates/preview/<slug:slug>/', views.TemplatePreviewView.as_view(), name='template_preview'),
    path('templates/scan/', views.TemplateScanView.as_view(), name='template_scan'),
    
    # URLs para biblioteca de componentes
    path('components/', views.ComponentLibraryView.as_view(), name='component_library'),
    path('components/preview/<slug:slug>/', views.ComponentPreviewView.as_view(), name='component_preview'),
    
    # URLs para editor de layout
    path('layout/editor/<slug:slug>/', views.LayoutEditorView.as_view(), name='layout_editor'),
    path('layout/preview/<slug:slug>/', views.LayoutPreviewView.as_view(), name='layout_preview'),
    
    # URLs para editor de regiões
    path('region/editor/<slug:template_slug>/<slug:region_slug>/', 
         views.RegionEditorView.as_view(), name='region_editor'),
    
    # URLs para editor de áreas de widgets
    path('widget-area/editor/<slug:template_slug>/<slug:area_slug>/', 
         views.WidgetAreaEditorView.as_view(), name='widget_area_editor'),
    
    # APIs para manipulação de componentes
    path('api/region/<slug:template_slug>/<slug:region_slug>/component/add/', 
         views.add_component_to_region, name='add_component_to_region'),
    path('api/component-instance/<int:instance_id>/update/', 
         views.update_component_instance, name='update_component_instance'),
    path('api/region/<slug:template_slug>/<slug:region_slug>/reorder/', 
         views.reorder_components, name='reorder_components'),
    path('api/component-instance/<int:instance_id>/delete/', 
         views.delete_component_instance, name='delete_component_instance'),
    
    # APIs para manipulação de widgets
    path('api/widget-area/<slug:template_slug>/<slug:area_slug>/widget/add/', 
         views.add_widget_to_area, name='add_widget_to_area'),
    path('api/widget-instance/<int:instance_id>/update/', 
         views.update_widget_instance, name='update_widget_instance'),
    path('api/widget-area/<slug:template_slug>/<slug:area_slug>/reorder/', 
         views.reorder_widgets, name='reorder_widgets'),
    path('api/widget-instance/<int:instance_id>/delete/', 
         views.delete_widget_instance, name='delete_widget_instance'),
]