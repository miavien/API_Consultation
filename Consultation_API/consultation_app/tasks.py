from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import User
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
