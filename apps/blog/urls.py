from django.urls import path
from . import views

urlpatterns = [
    path('', views.BlogListView.as_view(), name='blog'),
    path('<int:post_id>/', views.blog_detail, name='blog_detail'),
]