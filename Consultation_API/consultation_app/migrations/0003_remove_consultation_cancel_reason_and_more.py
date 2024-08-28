# Generated by Django 5.1 on 2024-08-28 05:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultation_app', '0002_consultation_is_completed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='consultation',
            name='cancel_reason',
        ),
        migrations.AddField(
            model_name='consultation',
            name='cancel_comment',
            field=models.CharField(blank=True, max_length=255, verbose_name='Комментарий при отмене'),
        ),
        migrations.AddField(
            model_name='consultation',
            name='cancel_reason_choice',
            field=models.CharField(blank=True, choices=[('Health', 'Здоровье'), ('Personal', 'Личное'), ('Found_another_specialist', 'Нашёл другого специалиста'), ('Other', 'Другое')], max_length=50, verbose_name='Причина отмены из списка'),
        ),
        migrations.AddField(
            model_name='consultation',
            name='status',
            field=models.CharField(choices=[('Pending', 'Ожидает'), ('Accepted', 'Принят'), ('Rejected', 'Отклонён')], default='Pending', max_length=15, verbose_name='Статус'),
        ),
    ]
