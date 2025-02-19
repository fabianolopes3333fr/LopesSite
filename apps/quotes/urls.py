from django.urls import path
from . import views

urlpatterns = [
    path('shop/', views.PaintCatalogView.as_view(), name='paint_catalog'),
    path('shop/paint/<slug:slug>/', views.PaintDetailView.as_view(), name='paint_detail'),
    
    path('request/', views.quote_request, name='request_quote'),
    path('confirmation/<int:quote_id>/', views.quote_confirmation, name='confirmation'),
    path('status/<int:quote_id>/', views.quote_status, name='status'),
    path('admin/update-status/<int:quote_id>/', views.admin_update_status, name='admin_update_status'),
]
