from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Application, UserAnalytics


@receiver(post_save, sender=User)
def create_user_analytics(sender, instance, created, **kwargs):
    if created:
        UserAnalytics.objects.create(user=instance)


@receiver(post_save, sender=Application)
def update_user_analytics(sender, instance, created, **kwargs):
    user = instance.user

    analytics, _ = UserAnalytics.objects.get_or_create(user=user)

    analytics.total_applications = Application.objects.filter(user=user).count()
    analytics.total_interviews = Application.objects.filter(
        user=user, status='interview'
    ).count()
    analytics.total_offers = Application.objects.filter(
        user=user, status='offer'
    ).count()

    analytics.save()