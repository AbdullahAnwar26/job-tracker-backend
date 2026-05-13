import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError



# =========================
# 1. Custom User Model
# =========================
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)

    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username


# =========================
# 2. Company Model
# =========================
class Company(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='companies')
    name = models.CharField(max_length=255)
    website = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'name'], name='unique_user_company')
        ]
    def __str__(self):
        return self.name


# =========================
# 3. Job Model (Global)
# =========================
class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    JOB_TYPE_CHOICES = (
        ('full_time', 'Full Time'),
        ('internship', 'Internship'),
        ('contract', 'Contract'),
    )

    title = models.CharField(max_length=255)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='jobs'
    )

    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)

    job_type = models.CharField(
        max_length=50,
        choices=JOB_TYPE_CHOICES,
        default='full_time'
    )

    url = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'company'],
                name='unique_job_per_company'
            )
        ]

    def __str__(self):
        return f"{self.title} - {self.company.name}"


# =========================
# 4. Application Model
# =========================
class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    STATUS_CHOICES = (
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('interview', 'Interview'),
        ('offer', 'Offer'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')

    applied_date = models.DateField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    is_deleted = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'job'], name='unique_user_job')
        ]
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['applied_date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.job.title}"


# =========================
# 5. Application Status History
# =========================
class ApplicationStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='history')
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)

    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application.id}: {self.old_status} → {self.new_status}"


# =========================
# 6. Notes Model
# =========================
class Note(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note for {self.application.id}"


# =========================
# 7. Reminder Model
# =========================
class Reminder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='reminders')
    title = models.CharField(max_length=100)
    message = models.CharField(max_length=255)

    remind_at = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reminder for {self.application.id} at {self.remind_at}"


# =========================
# 8. File Upload Model
# =========================
import os
import magic
from django.core.exceptions import ValidationError


def validate_file_extension(value):
    """
    Validate both:
    1. File extension
    2. MIME type
    """

    valid_extensions = ['.pdf', '.doc', '.docx']

    valid_mime_types = [
        'application/pdf',

        'application/msword',

        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]

    ext = os.path.splitext(value.name)[1].lower()

    if ext not in valid_extensions:
        raise ValidationError("Unsupported file extension.")

    # Read first bytes for MIME detection
    file_mime = magic.from_buffer(value.read(2048), mime=True)

    # Reset pointer after reading
    value.seek(0)

    if file_mime not in valid_mime_types:
        raise ValidationError("Invalid file type.")


class ApplicationFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='applications/', validators=[validate_file_extension])
    file_type = models.CharField(max_length=50)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for {self.application.id}"


# =========================
# 9. User Analytics
# =========================
class UserAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_applications = models.IntegerField(default=0)
    total_interviews = models.IntegerField(default=0)
    total_offers = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics for {self.user.username}"


# =========================
# 10. API Logs
# =========================
class APILog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)

    response_status = models.IntegerField()
    response_time = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.response_status}"
    

class EmailOTP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(db_index=True)
    otp = models.CharField(max_length=6)

    attempts = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['email', 'is_verified']),
        ]