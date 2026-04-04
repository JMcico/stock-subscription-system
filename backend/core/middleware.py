"""
Redirect `/api/...` paths missing a trailing slash to the same path with `/`
using HTTP 308 so POST/PUT/PATCH bodies are preserved (RFC 7538).
`APPEND_SLASH` alone can use 301/302 for some cases, which is unsafe for POST.
"""

from django.http import HttpResponse


class EnsureApiTrailingSlashMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith('/api') and path != '/' and not path.endswith('/'):
            query = request.META.get('QUERY_STRING', '')
            location = path + '/' + ('?' + query if query else '')
            response = HttpResponse(status=308)
            response['Location'] = location
            return response
        return self.get_response(request)
