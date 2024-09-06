from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *
from .tasks import *
@receiver(post_save, sender=Slot)
def send_notify(sender, instance, created, **kwargs):
    if created:
        specialist_email = instance.specialist.email
        send_email_task.delay(specialist_email)