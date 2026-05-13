import time
from .models import APILog

class APILogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()

        response = self.get_response(request)

        duration = time.time() - start

        try:
            APILog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                endpoint=request.path,
                method=request.method,
                response_status=response.status_code,
                response_time=duration
            )
        except Exception:
            pass  # never break request cycle
        

        return response