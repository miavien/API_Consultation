# Generated by Django 5.1 on 2024-09-06 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultation_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
