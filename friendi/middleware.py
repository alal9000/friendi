from django.http import HttpResponse


class UnderConstructionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Return an "Under Construction" response for all requests
        return HttpResponse(
            "<h1 style='text-align:center; margin-top:50px;'>Under Construction</h1><p style='text-align:center;'>We'll be back soon!</p>",
            content_type="text/html",
            status=503,  # Service Unavailable
        )
