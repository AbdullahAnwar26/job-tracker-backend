import json
import hashlib

from .models import Note, Reminder, User, Job, Company, Application, ApplicationFile, UserAnalytics  # explicit
from .serializers import (
    JobSerializer,
    RegisterRequestSerializer,
    CompanySerializer,
    ApplicationSerializer,
    ApplicationCreateSerializer,
    ApplicationUpdateSerializer,
    NoteSerializer,
    ReminderSerializer,
    ApplicationFileSerializer,
    UserAnalyticsSerializer,
    UserLoginSerializer
    
)

from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema

from django.core.cache import cache
from django.db import transaction

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .throttles import (
    SendOTPThrottle,
    VerifyOTPThrottle,
    LoginThrottle
)

# =========================
# Auth
# =========================
@extend_schema(
    tags=['Authentication']
)
class LoginView(TokenObtainPairView):
    serializer_class = UserLoginSerializer
    throttle_classes = [LoginThrottle]


# =========================
# Permissions
# =========================
class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


# =========================
# Company ViewSet
# =========================
class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Company.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# =========================
# Job ViewSet
# =========================
class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.select_related('company').all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['company', 'job_type']
    search_fields = ['title', 'company__name']

    def list(self, request):
        query_params = list(request.query_params.lists())

        if "page" not in request.query_params:
            query_params.append(("page", ["1"]))

        normalized = json.dumps(sorted(query_params), sort_keys=True)
        hashed = hashlib.md5(normalized.encode()).hexdigest()

        cache_key = f"job_list:user:{request.user.id}:{hashed}"

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        queryset = self.filter_queryset(self.get_queryset())
        page_obj = self.paginate_queryset(queryset)

        if page_obj is not None:
            serializer = self.get_serializer(page_obj, many=True)
            response = self.get_paginated_response(serializer.data)
            cache.set(cache_key, response.data, timeout=300)
            return response

        serializer = self.get_serializer(queryset, many=True)
        response = self.get_paginated_response(serializer.data)
        cache.set(cache_key, response.data, timeout=300)
        return response

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save()
        cache.delete_pattern("jobtracker:job_list:user:*")

    @transaction.atomic
    def perform_update(self, serializer):
        serializer.save()
        cache.delete_pattern("jobtracker:job_list:user:*")

    def perform_destroy(self, instance):
        instance.delete()
        cache.delete_pattern("jobtracker:job_list:user:*")


# =========================
# Application ViewSet
# =========================
class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    lookup_field = 'id'

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'job__company']
    search_fields = ['job__title', 'job__company__name']
    ordering_fields = ['applied_date', 'last_updated']

    def get_queryset(self):
        return Application.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).select_related('job__company').prefetch_related(
            'notes', 'files', 'reminders', 'history'
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return ApplicationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ApplicationUpdateSerializer
        return ApplicationSerializer

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()
        cache.delete(f"dashboard_{self.request.user.id}")

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()
        cache.delete(f"dashboard_{self.request.user.id}")


# =========================
# Notes ViewSet
# =========================
class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Note.objects.filter(application__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()


# =========================
# Reminder ViewSet
# =========================
class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Reminder.objects.filter(application__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()


# =========================
# File Upload ViewSet
# =========================
from rest_framework.parsers import MultiPartParser, FormParser
class ApplicationFileViewSet(viewsets.ModelViewSet):
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = ApplicationFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return ApplicationFile.objects.filter(application__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()


# =========================
# Dashboard
# =========================
@extend_schema(
    tags=['Dashboard']
)
class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        cache_key = f"dashboard_{user.id}"

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        qs = Application.objects.filter(user=user, is_deleted=False)

        total = qs.count()
        interviews = qs.filter(status='interview').count()
        offers = qs.filter(status='offer').count()

        success_rate = (offers / total * 100) if total > 0 else 0

        data = {
            "total_applications": total,
            "interviews": interviews,
            "offers": offers,
            "success_rate": round(success_rate, 2)
        }

        cache.set(cache_key, data, timeout=300)

        return Response(data)


# =========================
# Analytics
# =========================
class UserAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserAnalytics.objects.all()
    serializer_class = UserAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return UserAnalytics.objects.filter(user=self.request.user)



# =========================
# Logout
# =========================
from rest_framework import serializers, status
from rest_framework import generics
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class LogoutAPIView(generics.GenericAPIView):
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = serializer.validated_data["refresh"]

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Logged out successfully"},
                status=status.HTTP_200_OK
            )

        except TokenError:
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST
            )
        


from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import EmailOTP, User
from .serializers import RegisterRequestSerializer
from .utils import generate_otp, send_otp_email

@extend_schema(
    request=RegisterRequestSerializer,
    responses={200: None},
    tags=['Authentication']
)
class SendOTPAPIView(APIView):
    permission_classes = [AllowAny]

    throttle_classes = [SendOTPThrottle]

    def post(self, request):
        serializer = RegisterRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data['email'].lower()

        # 🚫 IP rate limit (5 requests / 5 min)
        ip = request.META.get("REMOTE_ADDR")
        cache_key = f"otp_limit:{ip}"

        request_count = cache.get(cache_key, 0)
        if request_count >= 5:
            return Response({"error": "Too many OTP requests. Try later."}, status=429)

        cache.set(cache_key, request_count + 1, timeout=300)

        # 🔒 30 sec resend restriction
        last_otp = EmailOTP.objects.filter(email=email).order_by('-created_at').first()

        if last_otp and (timezone.now() - last_otp.created_at).total_seconds() < 30:
            return Response({"error": "Wait 30 seconds before requesting again"}, status=429)

        otp = generate_otp()

        try:
            with transaction.atomic():
                EmailOTP.objects.create(email=email, otp=otp)
                send_otp_email(email, otp)
        except Exception:
            return Response({"error": "Failed to send OTP"}, status=500)

        return Response({"message": "OTP sent successfully"})
    


from datetime import timedelta
from django.utils import timezone
from django.db import transaction, IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import EmailOTP, User
from .serializers import VerifyOTPSerializer


@extend_schema(
    request=VerifyOTPSerializer,
    responses={201: None},
    tags=['Authentication']
)
class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    throttle_classes = [VerifyOTPThrottle]

    @transaction.atomic
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data['email'].lower()
        otp = serializer.validated_data['otp']
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already taken"}, status=400)

        # 🔐 LOCK latest OTP row (prevents race condition)
        otp_obj = EmailOTP.objects.select_for_update().filter(
            email=email,
            is_verified=False
        ).order_by('-created_at').first()

        if not otp_obj:
            return Response({"error": "Invalid OTP"}, status=400)

        # 🚫 brute force protection
        if otp_obj.attempts >= 5:
            return Response({"error": "Too many attempts"}, status=429)

        # ❌ wrong OTP
        if otp_obj.otp != otp:
            otp_obj.attempts += 1
            otp_obj.save(update_fields=["attempts"])
            return Response({"error": "Invalid OTP"}, status=400)

        # ⏳ expiry check (5 minutes)
        if (timezone.now() - otp_obj.created_at) > timedelta(minutes=5):
            return Response({"error": "OTP expired"}, status=400)

        # ✅ mark verified
        otp_obj.is_verified = True
        otp_obj.save(update_fields=["is_verified"])

        # ✅ create user (race-safe)
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_verified=True
            )
        except IntegrityError:
            return Response({"error": "User already exists"}, status=400)

        # 🧹 cleanup OTPs
        EmailOTP.objects.filter(email=email).delete()

        return Response({"message": "User registered successfully"}, status=201)
