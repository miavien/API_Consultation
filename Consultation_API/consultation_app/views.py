from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, extend_schema_view
from .serializers import *
from .permissions import *


# Create your views here.
class LoginAPIView(APIView):
    serializer_class = LoginSerializer

    @extend_schema(
        summary='Авторизация',
        description='Метод для авторизации пользователя',
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                response=LoginSerializer,
                description='Авторизация успешна',
                examples=[
                    OpenApiExample(
                        'Авторизация успешна',
                        value={'message': 'Авторизация успешна'})
                ]
            ),
            400: OpenApiResponse(
                response=LoginSerializer,
                description='Ошибка авторизации',
                examples=[
                    OpenApiExample(
                        'Ошибка авторизации',
                        value={'message': 'Неверные логин и/или пароль'}
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
                    'password': 'password123'
                },
                status_codes=[str(status.HTTP_202_ACCEPTED)],
            )
        ],
        tags=['For everyone']
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return Response({'message': 'Авторизация успешна'}, status=status.HTTP_200_OK)
            return Response({'message': 'Неверные логин и/или пароль'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
                    return Response({'message': 'Пользователь заблокирован'}, status=status.HTTP_200_OK)
                return Response({'message': 'Пользователь с таким id уже заблокирован'},
                                status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({'message': 'Пользователь с таким id не найден'}, status=status.HTTP_400_BAD_REQUEST)
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
                    return Response({'message': 'Пользователь разблокирован'}, status=status.HTTP_200_OK)
                else:
                    return Response({'message': 'Пользователь с таким id не заблокирован'},
                                    status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({'message': 'Пользователь с таким id не найден'}, status=status.HTTP_400_BAD_REQUEST)
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
                        value={'message': 'Слот успешно создан',
                               'data': {
                                   'date': '2024-09-05',
                                   'start_time': '13:00',
                                   'end_time': '13:30',
                                   'context': 'Доп. информация'
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
                        value={'detail': 'Дата не может быть ранее сегодняшнего дня'}
                    ),
                    OpenApiExample(
                        'Некорректное время',
                        value={'detail': 'Время окончания должно быть позже времени начала'}
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
            return Response({'message': 'Слот успешно создан', 'data': slot_serializer.data}, status=status.HTTP_200_OK)
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
                        value={"date": "2024-08-30",
                               "start_time": "10:00:00",
                               "end_time": "11:00:00",
                               "context": "",
                               "is_available": True,
                               "duration": "1h 0m"
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
                        value={"id": 14,
                               "specialist_username": "user1",
                               "date": "2024-09-03",
                               "start_time": "13:00:00",
                               "end_time": "14:30:00",
                               "context": "Платная услуга",
                               "duration": "1h 30m"
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
        return Slot.objects.filter(is_available=True)


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
                                "specialist_username": "user1",
                                "date": "2024-09-03",
                                "start_time": "13:00:00",
                                "end_time": "14:30:00",
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
                        value={'detail': 'Слота с таким id не существует'}
                    ),
                    OpenApiExample(
                        'Повторный запрос',
                        value={'message': 'Вы уже отправили запрос на консультацию на эту дату'}
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
                return Response({'message': 'Для данного слота уже существует подтверждённая консультация'})

            if Consultation.objects.filter(slot_id=slot_id, client=request.user):
                return Response({'message': 'Вы уже отправили запрос на консультацию на эту дату'})

            slot = Slot.objects.get(pk=slot_id)
            consultation_data = {
                'slot': slot,
                'client': request.user
            }
            consultation = Consultation.objects.create(**consultation_data)
            consultation_serializer = ConsultationSerializer(consultation)
            return Response(
                {'message': 'Запрос на консультацию успешно отправлен', 'data': consultation_serializer.data},
                status=status.HTTP_200_OK)

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
                               "status_display": "Ожидает"
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
