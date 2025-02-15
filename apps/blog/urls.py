from django.urls import path
from .views import BlogListView, BlogDetailView, CategoryPostListView, TagPostListView, SearchView



urlpatterns = [
    path('', BlogListView.as_view(), name='blog_list'),
    path('<slug:slug>/', BlogDetailView.as_view(), name='blog_detail'),
    path('<slug:slug>/comment/', BlogDetailView.as_view, name='add_comment'),
    path('category/<slug:slug>/', CategoryPostListView.as_view(), name='category_posts'),
    path('tag/<slug:slug>/', TagPostListView.as_view(), name='tag_posts'),
    path('search/', SearchView.as_view(), name='search'),
]

