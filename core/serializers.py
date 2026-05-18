import mimetypes
import os
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Company,
    Job,
    Application,
    Note,
    ApplicationFile,
    Reminder,
    ApplicationStatusHistory,
    UserAnalytics
)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.shortcuts import get_object_or_404
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from django.db import transaction

User = get_user_model()


# =========================
# 1. User Serializer
# =========================
class UserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']


class RegisterRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User already exists")
        return value

    def validate(self, data):
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Username already exists")

        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already exists")

        return data


# =========================
# VerifyOtpSerializer
# =========================
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User already exists")
        return value


# =========================
# 2. Company Serializer
# =========================
class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


# =========================
# 3. Job Serializer
# =========================
class JobSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)

    company_id = serializers.UUIDField(
        write_only=True
    )

    job_type_display = serializers.CharField(
        source='get_job_type_display',
        read_only=True
    )

    class Meta:
        model = Job

        fields = [
            'id',
            'title',
            'company',
            'company_id',
            'description',
            'location',
            'job_type',
            'job_type_display',
            'url',
            'created_at'
        ]

    def validate(self, attrs):
        title = attrs.get('title')
        company_id = attrs.get('company_id')

        if Job.objects.filter(
            title__iexact=title,
            company_id=company_id
        ).exists():
            raise serializers.ValidationError(
                {
                    "job": "Job already exists for this company."
                }
            )

        return attrs

    def create(self, validated_data):
        company_id = validated_data.pop('company_id')

        company = get_object_or_404(
            Company,
            id=company_id
        )

        return Job.objects.create(
            company=company,
            **validated_data
        )

    def update(self, instance, validated_data):
        if 'company_id' in validated_data:
            company_id = validated_data.pop('company_id')

            instance.company = get_object_or_404(
                Company,
                id=company_id
            )

        return super().update(instance, validated_data)

# =========================
# 4. Note Serializer
# =========================
class NoteSerializer(serializers.ModelSerializer):
    application = serializers.PrimaryKeyRelatedField(
        queryset=Application.objects.all(),
        write_only=True
    )

    class Meta:
        model = Note
        fields = ['id', 'application', 'content', 'created_at']

    def create(self, validated_data):
        request = self.context['request']
        application = validated_data.pop('application')

        if application.user != request.user:
            raise serializers.ValidationError(
                {"application": "Invalid application"}
            )

        return Note.objects.create(
            application=application,
            **validated_data
        )


# =========================
# 5. File Serializer
# =========================
class ApplicationFileSerializer(serializers.ModelSerializer):
    application = serializers.PrimaryKeyRelatedField(
        queryset=Application.objects.all(),
        write_only=True
    )

    class Meta:
        model = ApplicationFile
        fields = ['id', 'file', 'file_type', 'application', 'uploaded_at']

    def validate_file(self, value):
        max_size = 5 * 1024 * 1024

        if value.size > max_size:
            raise serializers.ValidationError(
                "File size must be under 5MB."
            )

        ext = os.path.splitext(value.name)[1].lower()

        allowed_extensions = ['.pdf', '.doc', '.docx']

        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                "Only PDF, DOC and DOCX files are allowed."
            )

        return value

    def create(self, validated_data):
        request = self.context['request']
        application = validated_data.pop('application')

        if application.user != request.user:
            raise serializers.ValidationError(
                {"application": "Invalid application"}
            )

        return ApplicationFile.objects.create(
            application=application,
            **validated_data
        )


# =========================
# 6. Reminder Serializer
# =========================
class ReminderSerializer(serializers.ModelSerializer):
    application = serializers.PrimaryKeyRelatedField(
        queryset=Application.objects.all(),
        write_only=True
    )

    class Meta:
        model = Reminder
        fields = ['id', 'title', 'message', 'application', 'remind_at', 'is_sent']

    def create(self, validated_data):
        request = self.context['request']
        application = validated_data.pop('application')

        if application.user != request.user:
            raise serializers.ValidationError(
                {"application": "Invalid application"}
            )

        return Reminder.objects.create(
            application=application,
            **validated_data
        )


# =========================
# 7. Status History Serializer
# =========================
class ApplicationStatusHistorySerializer(serializers.ModelSerializer):

    old_status_display = serializers.CharField(
        source='get_old_status_display',
        read_only=True
    )

    new_status_display = serializers.CharField(
        source='get_new_status_display',
        read_only=True
    )

    class Meta:
        model = ApplicationStatusHistory
        fields = [
            'id',
            'old_status',
            'old_status_display',
            'new_status',
            'new_status_display',
            'changed_at'
        ]


# =========================
# 8. Application Serializer (WRITE)
# =========================
class ApplicationCreateSerializer(serializers.ModelSerializer):
    job = serializers.UUIDField()

    class Meta:
        model = Application
        fields = ['id', 'job', 'status']

    @transaction.atomic
    def create(self, validated_data):
        request = self.context['request']
        user = request.user

        job_id = validated_data.pop('job')

        job = get_object_or_404(Job, id=job_id)

        application = Application.objects.create(
            user=user,
            job=job,
            **validated_data
        )

        ApplicationStatusHistory.objects.create(
            application=application,
            old_status='none',
            new_status=application.status
        )

        return application


# =========================
# 9. Application Serializer (READ - FULL)
# =========================
class ApplicationSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    notes = NoteSerializer(many=True, read_only=True)
    files = ApplicationFileSerializer(many=True, read_only=True)
    reminders = ReminderSerializer(many=True, read_only=True)
    history = ApplicationStatusHistorySerializer(many=True, read_only=True)

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = Application
        fields = [
            'id',
            'job',
            'status',
            'status_display',
            'applied_date',
            'last_updated',
            'notes',
            'files',
            'reminders',
            'history'
        ]


# =========================
# 10. Application Update Serializer
# =========================
class ApplicationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['status']

    def validate_status(self, value):
        valid = [choice[0] for choice in Application.STATUS_CHOICES]

        if value not in valid:
            raise serializers.ValidationError("Invalid status")

        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get('status', old_status)

        if old_status != new_status:
            ApplicationStatusHistory.objects.create(
                application=instance,
                old_status=old_status,
                new_status=new_status
            )

        return super().update(instance, validated_data)


# =========================
# 11. Analytics Serializer
# =========================
class UserAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnalytics
        fields = '__all__'


from django.contrib.auth import authenticate
from django.db.models import Q
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserLoginSerializer(TokenObtainPairSerializer):
    username_field = "username_or_email"

    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username_or_email = attrs.get("username_or_email")
        password = attrs.get("password")

        user = User.objects.filter(
            Q(username__iexact=username_or_email) |
            Q(email__iexact=username_or_email)
        ).first()

        if not user:
            raise serializers.ValidationError({
                "detail": "Invalid credentials"
            })

        authenticated_user = authenticate(
            username=user.username,
            password=password
        )

        if not authenticated_user:
            raise serializers.ValidationError({
                "detail": "Invalid credentials"
            })

        if not authenticated_user.is_verified:
            raise serializers.ValidationError({
                "detail": "Email not verified"
            })

        data = super().validate({
            "username_or_email": authenticated_user.username,
            "password": password
        })

        data["user"] = {
            "id": str(authenticated_user.id),
            "username": authenticated_user.username,
            "email": authenticated_user.email,
        }

        return data