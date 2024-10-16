from typing import Dict, Any, Optional

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from .tasks import *
from django.utils import timezone
from .models import *


#
# class LoginSerializer(serializers.Serializer):
#     username = serializers.CharField()
#     password = serializers.CharField(write_only=True)


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    raw_password = None

    class Meta:
        model = User
        fields = ['username', 'password', 'password_confirm', 'email', 'role']

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Этот email уже используется')
        return value

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError('Пароли не совпадают')
        return data

    def create(self, validated_data: Dict[str, Any]) -> User:
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')
        user = User(**validated_data)
        user.set_password(password)
        user.activation_token = uuid.uuid4()
        user.save()
        self.raw_password = password
        return user


class BlockUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class SlotSerializer(serializers.ModelSerializer):
    context = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Slot
        fields = ['id', 'date', 'start_time', 'end_time', 'duration', 'context']

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError({'detail': 'Время окончания должно быть позже времени начала'})

        if data['date'] < timezone.now().date():
            raise serializers.ValidationError({'detail': 'Дата не может быть ранее сегодняшнего дня'})

        now = timezone.now()
        if data['date'] == now.date() and data['start_time'] <= now.time():
            raise serializers.ValidationError({'detail': 'Нельзя создать слот на прошедшее время'})

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


class SpecialistSlotListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ['id', 'date', 'start_time', 'end_time', 'duration', 'context', 'is_available']


class ClientSlotListSerializer(serializers.ModelSerializer):
    specialist_username = serializers.CharField(source='specialist.username')

    class Meta:
        model = Slot
        fields = ['id', 'specialist_username', 'date', 'start_time', 'end_time', 'duration', 'context']


class ConsultationSerializer(serializers.ModelSerializer):
    slot_id = serializers.IntegerField(write_only=True)
    specialist_username = serializers.CharField(source='slot.specialist.username', read_only=True)
    date = serializers.DateField(source='slot.date', read_only=True)
    start_time = serializers.TimeField(source='slot.start_time', read_only=True)
    end_time = serializers.TimeField(source='slot.end_time', read_only=True)
    duration = serializers.DurationField(source='slot.duration', read_only=True)
    status_display = serializers.SerializerMethodField()
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Consultation
        fields = ['id', 'slot_id', 'specialist_username', 'date', 'start_time',
                  'end_time', 'duration', 'status_display']
        read_only_fields = ['client', 'is_canceled', 'cancel_comment',
                            'cancel_reason_choice', 'is_completed', 'status']

    @extend_schema_field(serializers.CharField)
    def get_status_display(self, obj):
        return obj.get_status_display()


class SpecialistConsultationListSerializer(serializers.ModelSerializer):
    slot_id = serializers.IntegerField(source='slot.id', read_only=True)
    date = serializers.DateField(source='slot.date', read_only=True)
    start_time = serializers.TimeField(source='slot.start_time', read_only=True)
    end_time = serializers.TimeField(source='slot.end_time', read_only=True)
    client_username = serializers.CharField(source='client.username', read_only=True)
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Consultation
        fields = ['id', 'slot_id', 'client_username', 'date', 'start_time', 'end_time', 'status_display', 'is_canceled',
                  'is_completed']

    def get_status_display(self, obj):
        return obj.get_status_display()


class ClientConsultationListSerializer(serializers.ModelSerializer):
    date = serializers.DateField(source='slot.date', read_only=True)
    start_time = serializers.TimeField(source='slot.start_time', read_only=True)
    end_time = serializers.TimeField(source='slot.end_time', read_only=True)
    specialist_username = serializers.CharField(source='slot.specialist.username', read_only=True)
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Consultation
        fields = ['id', 'specialist_username', 'date', 'start_time', 'end_time', 'status_display', 'is_canceled']

    def get_status_display(self, obj):
        return obj.get_status_display()


class UpdateStatusConsultationSerializer(serializers.ModelSerializer):
    consultation_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=Consultation.STATUS_CHOICE)

    class Meta:
        model = Consultation
        fields = ['consultation_id', 'status']

    def validate_status(self, value: str) -> str:
        if value not in dict(Consultation.STATUS_CHOICE).keys():
            raise serializers.ValidationError('Некорректный статус')
        return value

    def update(self, instance: Consultation, validated_data: Dict[str, Any]) -> Consultation:
        status = validated_data.get('status', instance.status)

        if status == 'Accepted':
            slot = instance.slot
            slot.is_available = False
            slot.save()

            Consultation.objects.filter(slot=slot).exclude(id=instance.id).update(status='Rejected')
            send_accepted_status_email.delay(instance.id)

        if status == 'Rejected':
            send_rejected_status_email.delay(instance.id)

        instance.status = status
        instance.save(update_fields=['status'])
        return instance


class SlotUpdateSerializer(serializers.ModelSerializer):
    specialist_username = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Slot
        fields = ['id', 'specialist_username', 'date', 'start_time', 'end_time', 'duration', 'context', 'is_available']
        read_only_fields = ['id', 'is_available', 'specialist', 'duration']

    def get_specialist_username(self, obj: Slot) -> Optional[str]:
        return obj.specialist.username if obj.specialist else None

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if start_time is not None and end_time is not None:
            if end_time <= start_time:
                raise serializers.ValidationError({'detail': 'Время окончания должно быть позже времени начала'})

        # Проверка на то, что дата не может быть ранее сегодняшнего дня
        if 'date' in data and data['date'] < timezone.now().date():
            raise serializers.ValidationError({'detail': 'Дата не может быть ранее сегодняшнего дня'})

        # Проверка на то, что на сегодняшнюю дату нельзя ставить время, которое уже прошло
        if 'date' in data and data['date'] == timezone.now().date():
            now = timezone.now()
            if 'start_time' in data and start_time <= now.time():
                raise serializers.ValidationError({'detail': 'Нельзя создать слот на прошедшее время'})

        return data

    def update(self, instance: Slot, validated_data: Dict[str, Any]) -> Slot:
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

    def _validate_slot_time(self, new_specialist: User, data: Dict[str, Any], instance: Slot) -> None:
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


class CancelConsultationSerializer(serializers.ModelSerializer):
    consultation_id = serializers.IntegerField()
    cancel_reason = serializers.ChoiceField(choices=Consultation.CANCEL_CHOICE, required=False)
    cancel_comment = serializers.CharField(required=False, max_length=255)

    class Meta:
        model = Consultation
        fields = ['consultation_id', 'cancel_reason', 'cancel_comment']

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cancel_reason = data.get('cancel_reason')
        cancel_comment = data.get('cancel_comment')
        if not cancel_reason and not cancel_comment:
            raise serializers.ValidationError('Необходимо указать либо причину отмены, либо оставить комментарий')
        return data

    def validate_cancel_reason(self, value: Optional[str]) -> Optional[str]:
        if value not in dict(Consultation.CANCEL_CHOICE).keys():
            raise serializers.ValidationError('Некорректная причина отмены')
        return value

    def update(self, instance: Consultation, validated_data: Dict[str, Any]) -> Consultation:
        instance.is_canceled = True
        instance.cancel_reason_choice = validated_data.get('cancel_reason', instance.cancel_reason_choice)
        instance.cancel_comment = validated_data.get('cancel_comment', instance.cancel_comment)
        instance.slot.is_available = True
        instance.slot.save()
        instance.save()
        return instance
