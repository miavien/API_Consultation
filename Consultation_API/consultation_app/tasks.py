from datetime import timezone
from django.utils import timezone
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import *


@shared_task
def send_confirmation_email(user_id):
    user = User.objects.get(id=user_id)
    confirmation_url = f'{settings.SITE_URL}/confirm/{user.activation_token}/'
    send_mail(
        subject='Подтверждение регистрации',
        message=(
            f'Здравствуйте, {user.username}!\n\n'
            f'Пожалуйста, подтвердите вашу регистрацию, перейдя по следующей ссылке: {confirmation_url}\n\n'
            f'Ваш логин: {user.username}\n'
            f'Ваш пароль: {user.password}\n'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email]
    )


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
