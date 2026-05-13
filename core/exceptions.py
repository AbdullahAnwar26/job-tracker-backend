from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.conf import settings
import traceback


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    # DRF handled exceptions
    if response is not None:
        return Response({
            "error": True,
            "message": response.data
        }, status=response.status_code)

    # DEBUG MODE → SHOW REAL ERROR
    if settings.DEBUG:
        return Response({
            "error": True,
            "exception_type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc()
        }, status=500)

    # PRODUCTION MODE
    return Response({
        "error": True,
        "message": "Something went wrong"
    }, status=500)