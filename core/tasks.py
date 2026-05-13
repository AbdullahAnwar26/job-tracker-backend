from celery import shared_task

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from datetime import timedelta

from .models import EmailOTP, APILog, Reminder


@shared_task
def send_reminders():
    """
    Send pending reminders via email
    """

    print("========== REMINDER TASK STARTED ==========")

    reminders = Reminder.objects.filter(
        remind_at__lte=timezone.now(),
        is_sent=False
    ).select_related('application__user')

    print(f"Pending reminders found: {reminders.count()}")

    sent_count = 0

    for reminder in reminders:

        try:

            user_email = reminder.application.user.email

            print(
                f"Sending reminder ID: {reminder.id} "
                f"to {user_email}"
            )

            send_mail(
                subject='Job Application Reminder',

                message=reminder.message,

                from_email=settings.EMAIL_HOST_USER,

                recipient_list=[user_email],

                fail_silently=False,
            )

            reminder.is_sent = True
            reminder.save(update_fields=['is_sent'])

            sent_count += 1

            print(
                f"Reminder {reminder.id} "
                f"marked as sent"
            )

        except Exception as e:

            print(
                f"ERROR sending reminder "
                f"{reminder.id}: {str(e)}"
            )

    print("========== REMINDER TASK FINISHED ==========")

    return f"{sent_count} reminders sent successfully"


@shared_task
def cleanup_old_otps():
    """
    Delete OTPs older than 24 hours
    """

    cutoff_time = timezone.now() - timedelta(hours=24)

    deleted_count, _ = EmailOTP.objects.filter(
        created_at__lt=cutoff_time
    ).delete()

    print(f"Deleted {deleted_count} old OTP records")

    return f"Deleted {deleted_count} old OTP records"


@shared_task
def cleanup_old_api_logs():
    """
    Delete API logs older than 30 days
    """

    cutoff_time = timezone.now() - timedelta(days=30)

    deleted_count, _ = APILog.objects.filter(
        created_at__lt=cutoff_time
    ).delete()

    print(f"Deleted {deleted_count} old API logs")

    return f"Deleted {deleted_count} API logs"