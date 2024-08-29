from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
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

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            slot_data = {
                'specialist': request.user,
                'date': validated_data['date'],
                'start_time': validated_data['start_time'],
                'end_time': validated_data['end_time']
            }
            if 'context' in validated_data:
                slot_data['context'] = validated_data['context']
            slot = Slot.objects.create(**slot_data)
            slot_serializer = SlotSerializer(slot)
            return Response({'message': 'Слот успешно создан', 'data': slot_serializer.data}, status=status.HTTP_200_OK)