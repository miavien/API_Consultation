from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *
from .tasks import *


# @receiver(post_save, sender=User)
# def user_post_save(sender, instance, created, **kwargs):
#     if created:
#         send_confirmation_email.delay(instance.id)
