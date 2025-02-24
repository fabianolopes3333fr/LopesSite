# apps/config/middleware.py
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from apps.config.models import Redirect

class ConfigCacheMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_staff and 'clear_cache' in request.GET:
            cache.clear()
            

class RedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        try:
            redirect_obj = Redirect.objects.get(old_path=path)
            return redirect(redirect_obj.new_path, permanent=True)
        except Redirect.DoesNotExist:
            return self.get_response(request)