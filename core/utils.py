import secrets
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404

def get_obj_or_404(model, **kwargs):
    return get_object_or_404(model, **kwargs)



def generate_otp():
    return str(secrets.randbelow(900000) + 100000)  # Generates a 6-digit OTP


def send_otp_email(email, otp):
    subject = "Your OTP Code"
    message = f"Your OTP is {otp}. It is valid for 5 minutes."

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )