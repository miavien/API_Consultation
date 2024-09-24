import logging
from datetime import timezone
from django.utils import timezone
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import *

logger = logging.getLogger(__name__)

@shared_task
def send_confirmation_email(user_id):

    try:
        user = User.objects.get(id=user_id)
        send_mail(
            'Confirmation Email',
            'Please confirm your registration.',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        logger.info(f"Confirmation email sent to: {user.email}")
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} does not exist.")


@shared_task
def send_accepted_status_email(consultation_id):
    consultation = Consultation.objects.get(id=consultation_id)
    user = consultation.client
    send_mail(
        subject='Изменение статуса консультации',
        message='Здравствуйте!\n\nСпециалист подтвердил вашу консультацию.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email]
    )


@shared_task
def send_rejected_status_email(consultation_id):
    consultation = Consultation.objects.get(id=consultation_id)
    user = consultation.client
    send_mail(
        subject='Изменение статуса консультации',
        message='Здравствуйте!\n\nСпециалист отклонил ваш запрос на консультацию.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email]
    )
