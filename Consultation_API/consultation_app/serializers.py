from django.utils import timezone
from rest_framework import serializers
from datetime import datetime
from .models import *


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class BlockUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class SlotSerializer(serializers.ModelSerializer):
    context = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Slot
        fields = ['date', 'start_time', 'end_time', 'duration', 'context']

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
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time
        )

        if same_time_slots.exists():
            raise serializers.ValidationError({'detail': 'Время слота пересекается с другим слотом'})

        return data

    def get_duration(self, obj):
        start_datetime = datetime.combine(obj.date, obj.start_time)
        end_datetime = datetime.combine(obj.date, obj.end_time)
        duration = end_datetime - start_datetime

        total_minutes = duration.total_seconds() // 60
        hours = total_minutes // 60
        minutes = total_minutes % 60

        return f'{int(hours)}h {int(minutes)}m'


class SpecialistSlotListSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Slot
        fields = ['id', 'date', 'start_time', 'end_time', 'context', 'is_available', 'duration']

    # метод для вычисления длительности слота
    def get_duration(self, obj):
        start_datetime = datetime.combine(obj.date, obj.start_time)
        end_datetime = datetime.combine(obj.date, obj.end_time)
        duration = end_datetime - start_datetime

        total_minutes = duration.total_seconds() // 60
        hours = total_minutes // 60
        minutes = total_minutes % 60

        return f'{int(hours)}h {int(minutes)}m'


class ClientSlotListSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()
    specialist_username = serializers.CharField(source='specialist.username')

    class Meta:
        model = Slot
        fields = ['id', 'specialist_username', 'date', 'start_time', 'end_time', 'context', 'duration']

    # метод для вычисления длительности слота
    def get_duration(self, obj):
        start_datetime = datetime.combine(obj.date, obj.start_time)
        end_datetime = datetime.combine(obj.date, obj.end_time)
        duration = end_datetime - start_datetime

        total_minutes = duration.total_seconds() // 60
        hours = total_minutes // 60
        minutes = total_minutes % 60

        return f'{int(hours)}h {int(minutes)}m'


class ConsultationSerializer(serializers.ModelSerializer):
    slot_id = serializers.IntegerField(write_only=True)
    specialist_username = serializers.CharField(source='slot.specialist.username', read_only=True)
    date = serializers.DateField(source='slot.date', read_only=True)
    start_time = serializers.TimeField(source='slot.start_time', read_only=True)
    end_time = serializers.TimeField(source='slot.end_time', read_only=True)
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Consultation
        fields = ['slot_id', 'specialist_username', 'date', 'start_time',
                  'end_time', 'status_display']
        read_only_fields = ['client', 'is_canceled', 'cancel_comment',
                            'cancel_reason_choice', 'is_completed', 'status']

    def validate_slot_id(self, value):
        if not Slot.objects.filter(id=value).exists():
            raise serializers.ValidationError('Слота с таким id не существует')
        return value

    def get_status_display(self, obj):
        return obj.get_status_display()


class SpecialistConsultationListSerializer(serializers.ModelSerializer):
    date = serializers.DateField(source='slot.date', read_only=True)
    start_time = serializers.TimeField(source='slot.start_time', read_only=True)
    end_time = serializers.TimeField(source='slot.end_time', read_only=True)
    client_username = serializers.CharField(source='client.username', read_only=True)
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Consultation
        fields = ['id', 'client_username', 'date', 'start_time', 'end_time', 'status_display']

    def get_status_display(self, obj):
        return obj.get_status_display()


class UpdateStatusConsultationSerializer(serializers.ModelSerializer):
    consultation_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=Consultation.STATUS_CHOICE)

    class Meta:
        model = Consultation
        fields = ['consultation_id', 'status']

    def validate_status(self, value):
        if value not in dict(Consultation.STATUS_CHOICE).keys():
            raise serializers.ValidationError('Некорректный статус')
        return value

    def validate_consultation_id(self, value):
        if not Consultation.objects.filter(id=value).exists():
            raise serializers.ValidationError('Консультации с таким id не существует')
        return value

    def update(self, instance, validated_data):
        status = validated_data.get('status', instance.status)

        if status == 'Accepted':
            slot = instance.slot
            slot.is_available = False
            slot.save()

            Consultation.objects.filter(slot=slot).exclude(id=instance.id).update(status='Rejected')

        instance.status = status
        instance.save()
        return instance


class SlotUpdateSerializer(serializers.ModelSerializer):
    specialist_username = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = Slot
        fields = ['id', 'specialist_username', 'date', 'start_time', 'end_time', 'context', 'is_available']
        read_only_fields = ['id', 'is_available', 'specialist']

    def get_specialist_username(self, obj):
        return obj.specialist.username if obj.specialist else None

    def update(self, instance, validated_data):
        specialist_username = validated_data.pop('specialist_username', None)
        new_specialist = instance.specialist

        if specialist_username:
            try:
                new_specialist = User.objects.get(username=specialist_username)
            except User.DoesNotExist:
                raise serializers.ValidationError({'specialist_username': 'Специалист с таким юзернеймом не найден'})

        self._validate_slot_time(new_specialist, validated_data, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def _validate_slot_time(self, new_specialist, data, instance):
        date = data.get('date', instance.date)
        start_time = data.get('start_time', instance.start_time)
        end_time = data.get('end_time', instance.end_time)

        same_time_slots = Slot.objects.filter(
            specialist=new_specialist,
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exclude(id=instance.id)

        if same_time_slots.exists():
            raise serializers.ValidationError({'detail': 'Время слота пересекается с другим слотом специалиста'})