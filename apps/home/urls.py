from django.urls import path
#from .views import HomePageView
from . import views

urlpatterns = [
    
    path('', views.home, name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('', views.testimonials_list, name='list'),
    path('submit/', views.submit_testimonial, name='submit_testimonial'),
    path('api/sync-google/', views.sync_google_reviews, name='sync_google'),
]
