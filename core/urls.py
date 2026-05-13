from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompanyViewSet,
    JobViewSet,
    ApplicationViewSet,
    NoteViewSet,
    ReminderViewSet,
    ApplicationFileViewSet,
    UserAnalyticsViewSet,
    SendOTPAPIView,
    VerifyOTPAPIView,
    LoginView,
    DashboardAPIView
) 
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='companies')
router.register(r'jobs', JobViewSet, basename='jobs')
router.register(r'applications', ApplicationViewSet, basename='applications')
router.register(r'notes', NoteViewSet, basename='notes')
router.register(r'reminders', ReminderViewSet, basename='reminders')
router.register(r'files', ApplicationFileViewSet, basename='files')

router.register(r'user-analytics', UserAnalyticsViewSet, basename='useranalytics')
urlpatterns = [
    path('', include(router.urls)),

    # Authentication
    path('sign-up/', SendOTPAPIView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPAPIView.as_view()),
    path('token/', LoginView.as_view(), name='token_obtain_pair'),

    # Dashboard
    path('dashboard/', DashboardAPIView.as_view(), name='dashboard'),

    # OpenAPI Schema
    path(
        'schema/',
        SpectacularAPIView.as_view(),
        name='schema'
    ),

    # Swagger Docs
    path(
        'docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui'
    ),

    # ReDoc
    path(
        'redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc'
    ),
]