from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *
from .tasks import *


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    if created:
        send_confirmation_email.delay(instance.id)


# @receiver(post_save, sender=Consultation)
# def accepted_consultation(sender, instance, created, **kwargs):
#     if not created:
#         update_fields = kwargs.get('update_fields', [])
#
#         # Проверяем, что поле 'status' было обновлено
#         if 'status' in update_fields:
#             old_instance = Consultation.objects.get(id=instance.id)
#             if old_instance.status != instance.status and instance.status == 'Accepted':
#                 send_accepted_status_email.delay(instance.id)