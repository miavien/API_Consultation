import logging
from datetime import datetime
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, extend_schema_view
from .serializers import *
from .permissions import *

logger = logging.getLogger(__name__)


class UserRegistrationAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Регистрация',
        description='Метод для регистрации пользователя. '
                    'Обязательные поля: username, password, password_confirm, role (Specialist/Client)',
        request=UserRegistrationSerializer,
        responses={
            200: OpenApiResponse(
                response=UserRegistrationSerializer,
                description='Регистрация успешна',
                examples=[
                    OpenApiExample(
                        'Регистрация успешна',
                        value={'message': 'Для подтверждения регистрации на указанную почту отправлено письмо'})
                ]
            ),
            400: OpenApiResponse(
                response=UserRegistrationSerializer,
                description='Ошибка регистрации',
                examples=[
                    OpenApiExample(
                        'Неверный пароль',
                        value={'non_field_errors': ['Пароли не совпадают']}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                'Пример запроса',
                description='Пример запроса',
                value={
                    'username': 'user1',
                    'email': 'my_email@mail.ru',
                    'password': 'password123',
                    'password_confirm': 'password123',
                    'role': 'Client'
                },
                status_codes=[str(status.HTTP_202_ACCEPTED)],
            )
        ],
        tags=['For everyone']
    )
    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            raw_password = serializer.raw_password
            send_confirmation_email.delay(user.id, raw_password)
            logger.info(f'User {request.data["username"]} has registered')
            return Response({'message': 'Для подтверждения регистрации на указанную почту отправлено письмо'},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConfirmRegistrationAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(exclude=True)
    def get(self, request, token, *args, **kwargs):
        user = get_object_or_404(User, activation_token=token)

        if user.is_active:
            return Response({'message': 'Ваш аккаунт уже активирован'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save()
        logger.info(f'User {user.username} has activated the account')
        return redirect('swagger-ui')


class BlockUserAPIView(APIView):
    serializer_class = BlockUserSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Блокировка',
        description='Метод для блокировки пользователя',
        request=BlockUserSerializer,
        responses={
            200: OpenApiResponse(
                response=BlockUserSerializer,
                description='Успешный запрос',
                examples=[
                    OpenApiExample(
                        'Успешный запрос',
                        value={'message': 'Пользователь заблокирован'})
                ]
            ),
            400: OpenApiResponse(
                response=BlockUserSerializer,
                description='Неверный запрос',
                examples=[
                    OpenApiExample(
                        'Неверный запрос_1',
                        value={'message': 'Пользователь с таким id уже заблокирован'}
                    ),
                    OpenApiExample(
                        'Неверный запрос_2',
                        value={'message': 'Пользователь с таким id не найден'}
                    ),
                ]
            )
        },
        examples=[
            OpenApiExample(
                'Пример запроса',
                description='Пример запроса',
                value={
                    'id': 1
                },
                status_codes=[str(status.HTTP_202_ACCEPTED)],
            )
        ],
        tags=['For admin']
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['id']
            try:
                user = User.objects.get(id=user_id)
                if user.is_blocked == False:
                    user.is_blocked = True
                    user.save()
                    logger.info(f'User {user.username} has been blocked')
                    return Response({'message': 'Пользователь заблокирован'}, status=status.HTTP_200_OK)
                logger.warning(f'User {user.username} is already blocked')
                return Response({'message': 'Пользователь с таким id уже заблокирован'},
                                status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                logger.warning(f'User with id {user_id} not exist')
                return Response({'message': 'Пользователь с таким id не найден'}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f'User block request failed validation: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnblockUserAPIView(APIView):
    serializer_class = BlockUserSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Разблокировка',
        description='Метод для разблокировки пользователя',
        request=BlockUserSerializer,
        responses={
            200: OpenApiResponse(
                response=BlockUserSerializer,
                description='Успешный запрос',
                examples=[
                    OpenApiExample(
                        'Успешный запрос',
                        value={'message': 'Пользователь разблокирован'})
                ]
            ),
            400: OpenApiResponse(
                response=BlockUserSerializer,
                description='Неверный запрос',
                examples=[
                    OpenApiExample(
                        'Неверный запрос_1',
                        value={'message': 'Пользователь с таким id не заблокирован'}
                    ),
                    OpenApiExample(
                        'Неверный запрос_2',
                        value={'message': 'Пользователь с таким id не найден'}
                    ),
                ]
            )
        },
        examples=[
            OpenApiExample(
                'Пример запроса',
                description='Пример запроса',
                value={
                    'id': 1
                },
                status_codes=[str(status.HTTP_202_ACCEPTED)],
            )
        ],
        tags=['For admin']
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['id']
            try:
                user = User.objects.get(id=user_id)
                if user.is_blocked:
                    user.is_blocked = False
                    user.save()
                    logger.info(f'User {user.username} has been unblocked')
                    return Response({'message': 'Пользователь разблокирован'}, status=status.HTTP_200_OK)
                else:
                    logger.warning(f'User {user.username} is not blocked')
                    return Response({'message': 'Пользователь с таким id не заблокирован'},
                                    status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                logger.warning(f'User with id {user_id} not exist')
                return Response({'message': 'Пользователь с таким id не найден'}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f'User block request failed validation: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateSlotAPIView(APIView):
    permission_classes = [IsSpecialistUser]
    serializer_class = SlotSerializer

    @extend_schema(
        summary='Создание слота',
        description='Метод для создания специалистом слотов для консультаций',
        request=SlotSerializer,
        responses={
            200: OpenApiResponse(
                response=SlotSerializer,
                description='Успешный запрос',
                examples=[
                    OpenApiExample(
                        'Успешный запрос',
                        value={"message": "Слот успешно создан",
                               "data": {
                                   "id": 17,
                                   "date": "2024-09-22",
                                   "start_time": "13:00:00",
                                   "end_time": "13:30:00",
                                   "duration": "00:30:00",
                                   "context": "Some context here"
                               }
                               }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=SlotSerializer,
                description='Неверный запрос',
                examples=[
                    OpenApiExample(
                        'Некорректная дата',
                        value={
                            'detail': [
                                'Дата не может быть ранее сегодняшнего дня'
                            ]
                        }
                    ),
                    OpenApiExample(
                        'Некорректное время',
                        value={
                            'detail': [
                                'Время окончания должно быть позже времени начала'
                            ]
                        }
                    ),
                    OpenApiExample(
                        'Некорректное время',
                        value={
                            'detail': [
                                'Время слота пересекается с другим слотом'
                            ]
                        }
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                'Пример запроса',
                description='Пример запроса',
                value={'date': '2024-09-05',
                       'start_time': '13:00',
                       'end_time': '13:30',
                       'context': 'Some context here'},
                status_codes=[str(status.HTTP_202_ACCEPTED)],
            )
        ],
        tags=['For specialist']
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            validated_data = serializer.validated_data
            slot_data = {
                'specialist': request.user,
                'date': validated_data['date'],
                'start_time': validated_data['start_time'],
                'end_time': validated_data['end_time'],
                'context': validated_data.get('context', None)
            }
            slot = Slot.objects.create(**slot_data)
            slot_serializer = SlotSerializer(slot)
            logger.info(f'Slot with id = {slot.id} has been created')
            return Response({'message': 'Слот успешно создан', 'data': slot_serializer.data}, status=status.HTTP_200_OK)
        logger.warning(f'Creating slot request failed validation: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        summary='Получение всех слотов',
        description='Получение специалистом всех личных слотов',
        tags=['For specialist'],
        responses={
            200: OpenApiResponse(
                response=SlotSerializer,
                description='Успешный запрос',
                examples=[
                    OpenApiExample(
                        'Успешный запрос',
                        value=
                        {"id": 10,
                         "date": "2024-09-22",
                         "start_time": "13:00:00",
                         "end_time": "13:30:00",
                         "duration": "00:30:00",
                         "context": "Some context here",
                         "is_available": True
                         }
                    )
                ]
            ),
        }
    )
)
class SpecialistSlotListView(ListAPIView):
    serializer_class = SpecialistSlotListSerializer
    permission_classes = [IsSpecialistUser]

    def get_queryset(self):
        return Slot.objects.filter(specialist=self.request.user)


@extend_schema_view(
    get=extend_schema(
        summary='Получение всех слотов',
        description='Получение клиентом всех доступных для записи слотов',
        tags=['For client'],
        responses={
            200: OpenApiResponse(
                response=SlotSerializer,
                description='Успешный запрос',
                examples=[
                    OpenApiExample(
                        'Успешный запрос',
                        value={"id": 10,
                               "specialist_username": "user3",
                               "date": "2024-09-23",
                               "start_time": "12:00:00",
                               "end_time": "13:00:00",
                               "duration": "01:00:00",
                               "context": "Some context here"
                               }
                    )
                ]
            ),
        }
    )
)
class ClientSlotListView(ListAPIView):
    serializer_class = ClientSlotListSerializer
    permission_classes = [IsClientUser]

    def get_queryset(self):
        now = timezone.now()
        # фильтруем, чтобы либо дата была больше сегодняшней, либо сегодня, но время старта больше текущего времени
        return Slot.objects.filter(
            Q(is_available=True) & (Q(date__gt=now.date()) | Q(date=now.date(), start_time__gte=now.time()))
        )


class ClientConsultationAPIView(APIView):
    permission_classes = [IsClientUser]
    serializer_class = ConsultationSerializer

    @extend_schema(
        summary='Создание запроса на консультацию',
        description='Метод для создания клиентом запроса на консультацию по id свободного слота',
        request=ConsultationSerializer,
        responses={
            200: OpenApiResponse(
                response=ConsultationSerializer,
                description='Успешный запрос',
                examples=[
                    OpenApiExample(
                        'Успешный запрос',
                        value={
                            "message": "Запрос на консультацию успешно отправлен",
                            "data": {
                                "id": 4,
                                "specialist_username": "user3",
                                "date": "2024-09-23",
                                "start_time": "12:00:00",
                                "end_time": "13:00:00",
                                "duration": "01:00:00",
                                "status_display": "Ожидает"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ConsultationSerializer,
                description='Неверный запрос',
                examples=[
                    OpenApiExample(
                        'Слот занят',
                        value={'message': 'Для данного слота уже существует подтверждённая консультация'}
                    ),
                    OpenApiExample(
                        'Некорректный id слота',
                        value={
                            'slot_id': [
                                'Слота с таким id не существует'
                            ]
                        }
                    ),
                    OpenApiExample(
                        'Повторный запрос',
                        value={'message': 'Вы уже отправили запрос на консультацию на эту дату'}
                    ),
                    OpenApiExample(
                        'Некорректное время',
                        value={'message': 'Дата и время консультации не могут быть ранее текущего времени'}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                'Пример запроса',
                description='Пример запроса',
                value={'slot_id': 1},
                status_codes=[str(status.HTTP_202_ACCEPTED)],
            )
        ],
        tags=['For client']
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            slot_id = serializer.validated_data['slot_id']
            if Consultation.objects.filter(slot_id=slot_id, status='Accepted').exists():
                logger.warning(f'Failed by user {request.user.username} for slot {slot_id}')
                return Response({'message': 'Для данного слота уже существует подтверждённая консультация'},
                                status=status.HTTP_400_BAD_REQUEST)

            if Consultation.objects.filter(slot_id=slot_id, client=request.user):
                logger.warning(f'Failed by User {request.user.username} for slot {slot_id}')
                return Response({'message': 'Вы уже отправили запрос на консультацию на эту дату'},
                                status=status.HTTP_400_BAD_REQUEST)

            now = datetime.now()
            slot = Slot.objects.get(pk=slot_id)
            slot_time = datetime.combine(slot.date, slot.start_time)
            if slot_time < now:
                logger.warning(f'Failed by User {request.user.username} for slot {slot_id}')
                return Response({'message': 'Дата и время консультации не могут быть ранее текущего времени'},
                                status=status.HTTP_400_BAD_REQUEST)

            consultation_data = {
                'slot': slot,
                'client': request.user
            }
            consultation = Consultation.objects.create(**consultation_data)
            consultation_serializer = ConsultationSerializer(consultation)
            logger.info(f'User {request.user.username} has created a consultation with id = {consultation.id}')
            return Response(
                {'message': 'Запрос на консультацию успешно отправлен', 'data': consultation_serializer.data},
                status=status.HTTP_200_OK)
        logger.warning(f'User {request.user.username} failed to book a consultation: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        summary='Получение всех консультаций',
        description='Получение специалистом всех личных консультаций',
        tags=['For specialist'],
        responses={
            200: OpenApiResponse(
                response=SlotSerializer,
                description='Успешный запрос',
                examples=[
                    OpenApiExample(
                        'Успешный запрос',
                        value={"id": 12,
                               "client_username": "client1",
                               "date": "2024-09-03",
                               "start_time": "13:00:00",
                               "end_time": "14:30:00",
                               "status_display": "Ожидает",
                               "is_canceled": False,
                               "is_completed": False
                               }
                    )
                ]
            ),
        }
    )
)
class SpecialistConsultationListView(ListAPIView):
    serializer_class = SpecialistConsultationListSerializer
    permission_classes = [IsSpecialistUser]

    def get_queryset(self):
        user = self.request.user
        return Consultation.objects.filter(slot__specialist=user)


@extend_schema_view(
    get=extend_schema(
        summary='Получение консультаций',
        description='Получение клиентом всех личных консультаций',
        tags=['For client'],
        responses={
            200: OpenApiResponse(
                response=SlotSerializer,
                description='Успешный запрос',
                examples=[
                    OpenApiExample(
                        'Успешный запрос',
                        value={
                            "id": 1,
                            "specialist_username": "user3",
                            "date": "2024-09-20",
                            "start_time": "13:00:00",
                            "end_time": "13:30:00",
                            "status_display": "Отклонён",
                            "is_canceled": False
                        }
                    )
                ]
            ),
        }
    )
)
class ClientConsultationListView(ListAPIView):
    serializer_class = ClientConsultationListSerializer
    permission_classes = [IsClientUser]

    def get_queryset(self):
        user = self.request.user
        return Consultation.objects.filter(client=user)


class UpdateStatusConsultationAPIView(APIView):
    permission_classes = [IsSpecialistUser]
    serializer_class = UpdateStatusConsultationSerializer

    @extend_schema(
        summary='Обновление статуса консультации',
        description='Метод для изменения специалистом статуса консультации на один из вариантов: Accepted/Rejected',
        request=UpdateStatusConsultationSerializer,
        responses={
            200: OpenApiResponse(
                response=UpdateStatusConsultationSerializer,
                description='Успешный запрос',
                examples=[
                    OpenApiExample(
                        'Успешный запрос',
                        value={
                            "message": "Статус консультации обновлён",
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=UpdateStatusConsultationSerializer,
                description='Неверный запрос',
                examples=[
                    OpenApiExample(
                        'Неверный статус',
                        value={'detail': 'Некорректный статус'}
                    ),
                    OpenApiExample(
                        'Некорректный id консультации',
                        value={
                            'consultation_id': [
                                'Консультации с таким id не существует'
                            ]
                        }
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                'Пример запроса',
                description='Пример запроса',
                value={'consultation_id': 1,
                       'status': 'Accepted'},
                status_codes=[str(status.HTTP_202_ACCEPTED)],
            )
        ],
        tags=['For specialist']
    )
    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            consultation_id = serializer.validated_data['consultation_id']
            consultation = Consultation.objects.get(id=consultation_id)
            serializer.update(consultation, serializer.validated_data)
            logger.info(f'Consultation with id = {consultation_id} has been updated successfully')
            return Response({'message': 'Статус консультации обновлён'}, status=status.HTTP_200_OK)
        logger.warning(f'Invalid data received for consultation update: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SlotUpdateAPIView(APIView):
    permission_classes = [IsSpecialistUser]

    @extend_schema(
        summary='Изменение параметров слота',
        description='Метод для изменения специалистом данных слота',
        request=SlotUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=SlotUpdateSerializer,
                description='Успешный запрос',
                examples=[
                    OpenApiExample(
                        'Успешный запрос',
                        value={
                            "message": "Слот успешно обновлен",
                            "data": {
                                "id": 16,
                                "date": "2024-09-05",
                                "start_time": "12:00:00",
                                "end_time": "12:30:00",
                                "context": None,
                                "is_available": True
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=SlotUpdateSerializer,
                description='Неверный запрос',
                examples=[
                    OpenApiExample(
                        'Некорректные данные',
                        value={'message': 'Необходимо указать id слота'}
                    ),
                    OpenApiExample(
                        'Некорректный id слота',
                        value={'message': 'Вашего слота с таким id не существует'}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                'Пример запроса',
                description='Пример запроса',
                value={"id": 1,
                       "date": "2024-09-05",
                       "start_time": "12:00:00",
                       "end_time": "13:00:00"},
                status_codes=[str(status.HTTP_202_ACCEPTED)],
            )
        ],
        tags=['For specialist']
    )
    def patch(self, request):
        slot_id = request.data.get('id')
        if not slot_id:
            logger.warning(f'Invalid data received for slot update for id={slot_id}')
            return Response({'message': 'Необходимо указать id слота'}, status=status.HTTP_400_BAD_REQUEST)

        slot = Slot.objects.filter(id=slot_id, specialist=request.user).first()

        if not slot:
            logger.warning(f'Slot with id={slot_id} is not exists')
            return Response({'message': 'Вашего слота с таким id не существует'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SlotUpdateSerializer(slot, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f'Slot with id = {slot_id} has been updated successfully')
            return Response({'message': 'Слот успешно обновлен', 'data': serializer.data}, status=status.HTTP_200_OK)
        logger.warning(f'Invalid data received for slot update: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CancelConsultationAPIView(APIView):
    permission_classes = [IsClientUser]
    serializer_class = CancelConsultationSerializer

    @extend_schema(
        summary='Отмена консультации',
        description='Метод для отмены клиентом консультации. Необходимо указать либо cancel_comment, '
                    'либо одну из причин в cancel_reason: Health/Personal/Found_another_specialist/Other',
        request=CancelConsultationSerializer,
        responses={
            200: OpenApiResponse(
                response=CancelConsultationSerializer,
                description='Успешный запрос',
                examples=[
                    OpenApiExample(
                        'Успешный запрос',
                        value={
                            "message": "Вы отменили консультацию",
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=CancelConsultationSerializer,
                description='Неверный запрос',
                examples=[
                    OpenApiExample(
                        'Некорректный запрос',
                        value={'detail': 'Необходимо указать либо причину отмены, либо оставить комментарий'}
                    ),
                    OpenApiExample(
                        'Некорректный id консультации',
                        value={'detail': 'Консультации с таким id не существует'}
                    ),
                    OpenApiExample(
                        'Некорректная причина',
                        value={'detail': 'Некорректная причина отмены'}
                    ),
                ]
            )
        },
        examples=[
            OpenApiExample(
                'Пример запроса',
                description='Пример запроса',
                value={'consultation_id': 1,
                       'cancel_reason': 'Other',
                       'cancel_comment': 'Передумал'},
                status_codes=[str(status.HTTP_202_ACCEPTED)],
            )
        ],
        tags=['For client']
    )
    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            consultation_id = serializer.validated_data['consultation_id']
            consultation = Consultation.objects.get(id=consultation_id)
            if consultation.client != request.user:
                logger.warning(f'Failed by user {request.user.username} to cancel consultation {consultation_id}')
                return Response(
                    {'message': 'Вы не можете отменить эту консультацию, так как вы не являетесь её клиентом'},
                    status=status.HTTP_403_FORBIDDEN)
            if consultation.is_canceled == True:
                logger.warning(f'Failed by user {request.user.username} to cancel consultation {consultation_id}')
                return Response({'message': 'Вы уже отменили консультацию'}, status=status.HTTP_400_BAD_REQUEST)
            serializer.update(consultation, serializer.validated_data)
            logger.info(f'User {request.user.username} has canceled consultation with id = {consultation_id}.')
            return Response({'message': 'Вы отменили консультацию'}, status=status.HTTP_200_OK)
        logger.warning(f'Invalid data provided for canceling consultation: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
