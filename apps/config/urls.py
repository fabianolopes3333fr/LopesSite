# apps/config/urls.py
from django.urls import path
from . import views

# app_name = 'config'

urlpatterns = [
    
    path('', views.dashboard_view_config, name='dashboard'),
    
    # Pages
    path('pages/', views.page_list, name='page_list'),
    path('<slug:slug>/', views.page_detail, name='page_detail'),
    path('pages/create/', views.page_create, name='page_create'),
    path('pages/<int:pk>/update/', views.page_update, name='page_update'),
    path('pages/<int:pk>/delete/', views.page_delete, name='page_delete'),
    # path('pages/<int:pk>/preview/', views.page_preview, name='page_preview'),
    
    # Styles
    path('styles/', views.style_list, name='style_list'),
    path('styles/create/', views.style_create, name='style_create'),
    path('styles/<int:pk>/update/', views.style_update, name='style_update'),
    path('styles/<int:pk>/delete/', views.style_delete, name='style_delete'),
    
    # Menus
    path('menus/', views.menu_list, name='menu_list'),
    path('menus/create/', views.menu_create, name='menu_create'),
    path('menus/<int:pk>/update/', views.menu_update, name='menu_update'),
    path('menus/<int:pk>/delete/', views.menu_delete, name='menu_delete'),
    path('menus/order/', views.menu_order, name='menu_order'),
    
]