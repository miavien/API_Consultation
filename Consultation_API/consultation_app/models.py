from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = [
        ('Admin', 'Админ'),
        ('Specialist', 'Специалист'),
        ('Client', 'Клиент'),
    ]

    role = models.CharField(max_length=15, choices=ROLE_CHOICES, verbose_name='Роль')
    is_blocked = models.BooleanField(default=False, verbose_name='Заблокирован')

    def __str__(self):
        return self.username

    def is_admin(self):
        return self.role == 'Admin'

    def is_specialist(self):
        return self.role == 'Specialist'

    def is_client(self):
        return self.role == 'Client'


class Slot(models.Model):
    specialist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='slots', verbose_name='Специалист')
    date = models.DateField(verbose_name='Дата', db_index=True)
    start_time = models.TimeField(verbose_name='Начало', db_index=True)
    end_time = models.TimeField(verbose_name='Окончание', db_index=True)
    duration = models.DurationField(blank=True, null=True, verbose_name='Длительность')
    context = models.CharField(max_length=255, blank=True, null=True, verbose_name='Контекст')
    is_available = models.BooleanField(default=True, verbose_name='Доступно', db_index=True)

    def __str__(self):
        return f'{self.specialist} {self.date} {self.start_time} - {self.end_time}'

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            start = timedelta(hours=self.start_time.hour, minutes=self.start_time.minute,
                              seconds=self.start_time.second)
            end = timedelta(hours=self.end_time.hour, minutes=self.end_time.minute,
                              seconds=self.end_time.second)
            self.duration = end - start
        super().save(*args, **kwargs)

class Consultation(models.Model):
    CANCEL_CHOICE = [
        ('Health', 'Здоровье'),
        ('Personal', 'Личное'),
        ('Found_another_specialist', 'Нашёл другого специалиста'),
        ('Other', 'Другое'),
    ]

    STATUS_CHOICE = [
        ('Pending', 'Ожидает'),
        ('Accepted', 'Принят'),
        ('Rejected', 'Отклонён'),
    ]

    slot = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name='consultations', verbose_name='Слот')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consultations', verbose_name='Клиент')
    is_canceled = models.BooleanField(default=False, verbose_name='Отменен')
    cancel_comment = models.CharField(max_length=255, blank=True, verbose_name='Комментарий при отмене')
    cancel_reason_choice = models.CharField(max_length=50, choices=CANCEL_CHOICE, blank=True,
                                            verbose_name='Причина отмены из списка')
    is_completed = models.BooleanField(default=False, verbose_name='Завершен')
    status = models.CharField(max_length=15, choices=STATUS_CHOICE, default='Pending', verbose_name='Статус', db_index=True)

    def __str__(self):
        return f'Specialist: {self.slot.specialist.username}, client: {self.client.username}'
