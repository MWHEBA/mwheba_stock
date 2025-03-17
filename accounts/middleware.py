from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from .models import ActivityLog
import re

class ActivityLogMiddleware(MiddlewareMixin):
    EXEMPT_URLS = [
        r'^/static/',
        r'^/media/',
        r'^/admin/jsi18n/',
    ]

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip if user is anonymous
        if isinstance(request.user, AnonymousUser):
            return None
        
        # Skip exempt URLs
        path = request.path_info.lstrip('/')
        for exempt_url in self.EXEMPT_URLS:
            if re.match(exempt_url, path):
                return None
        
        # Log the action
        if request.method in ['POST', 'PUT', 'DELETE'] and hasattr(view_func, '__name__'):
            action = f"{request.method} - {view_func.__name__}"
            model = view_kwargs.get('model', '')
            object_id = view_kwargs.get('pk')
            
            ActivityLog.objects.create(
                user=request.user,
                action=action,
                model=model,
                object_id=object_id
            )
            
        return None
