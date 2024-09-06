from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_email_task(email):
    send_mail(
        'New slot created',
        'Hiii',
        settings.DEFAULT_FROM_EMAIL,
        [email]
    )