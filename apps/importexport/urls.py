# urls.py para o aplicativo de importação/exportação
from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'importexport'

urlpatterns = [
    path('export/', views.export_list, name='export_list'),
    path('export/selected/', views.export_selected, name='export_selected'),
    path('import/', views.import_form, name='import_form'),
    path('import/preview/', views.import_preview, name='import_preview'),
    path('import/process/', views.import_process, name='import_process'),
    # Nova rota para documentação
    path('docs/', TemplateView.as_view(template_name='importexport/import_export_documentation.html'), name='documentation'),
]