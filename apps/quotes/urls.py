from django.urls import path
from . import views

urlpatterns = [
    path('shop/', views.PaintCatalogView.as_view(), name='paint_catalog'),
    path('shop/paint/<slug:slug>/', views.PaintDetailView.as_view(), name='paint_detail'),
    path('create/', views.create_quote, name='create_quote'),
    path('success/', views.quote_success, name='quote_success'),
]
