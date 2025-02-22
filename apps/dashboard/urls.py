from django.urls import path
from . import views

urlpatterns = [
    # urls.py
    path('', views.dashboard, name='dashboard'),
    path('dashboard/user/', views.user_dashboard, name='user_dashboard'),
    
    
]