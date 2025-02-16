from django.urls import path
from . import views

urlpatterns = [
    path('request/', views.request_quote, name='request_quote'),
    path('shop/', views.PaintCatalogView.as_view(), name='paint_catalog'),
    path('shop/paint/<slug:slug>/', 
         views.PaintDetailView.as_view(), 
         name='paint_detail'),
]
