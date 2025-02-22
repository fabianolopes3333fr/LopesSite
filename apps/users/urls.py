from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # urls.py
    path('two-factor-auth/', views.two_factor_auth, name='two_factor_auth'),
    path('profile/', views.profile, name='profile'),
    
    # section for newsletter signup
    path('newsletter/signup/', views.newsletter_signup, name='newsletter_signup'),
    
]