from datetime import date

from rest_framework import serializers
from .models import *


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class BlockUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class SlotSerializer(serializers.ModelSerializer):
    context = serializers.CharField(required=False)
    class Meta:
        model = Slot
        fields = ['date', 'start_time', 'end_time', 'context']

    def validate(self, data):
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError('Время окончания должно быть позже времени начала')

        if data['date'] < date.today():
            raise serializers.ValidationError('Дата не может быть ранее сегодняшнего дня')

        return data
