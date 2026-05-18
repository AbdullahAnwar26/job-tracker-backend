from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from core.views import LoginView, LogoutAPIView
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse


def home(request):
    return JsonResponse({
        "status": "success",
        "message": "Job Tracker API Running"
    })


urlpatterns = [
    path('', home),

    path('admin/', admin.site.urls),

    path('api/', include('core.urls')),

    path(
        'api/token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),

    path(
        'api/login/',
        LoginView.as_view(),
        name='login'
    ),

    path(
        'api/logout/',
        LogoutAPIView.as_view(),
        name='logout'
    ),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)