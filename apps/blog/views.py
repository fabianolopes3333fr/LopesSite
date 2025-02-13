from django.shortcuts import render, get_object_or_404
from .models import Post
from django.views.generic import ListView

class BlogListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'

def blog_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return render(request, 'blog/detail.html', {'post': post})
