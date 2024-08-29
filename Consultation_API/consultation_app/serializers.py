from django.utils import timezone
from rest_framework import serializers
from .models import *


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class BlockUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class SlotSerializer(serializers.ModelSerializer):
    context = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Slot
        fields = ['date', 'start_time', 'end_time', 'context']

    def validate(self, data):
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError({'detail': 'Время окончания должно быть позже времени начала'})

        if data['date'] < timezone.now().date():
            raise serializers.ValidationError({'detail': 'Дата не может быть ранее сегодняшнего дня'})

        # проверяем на пересечение времени слотов
        specialist = self.context['request'].user
        date = data['date']
        start_time = data['start_time']
        end_time = data['end_time']

        same_time_slots = Slot.objects.filter(
            specialist=specialist,
            date=date
        ).filter(
            start_time__lt=end_time,
            end_time__gt=start_time
        )

        if same_time_slots.exists():
            raise serializers.ValidationError({'detail': 'Время слота пересекается с другим слотом'})

        return data
