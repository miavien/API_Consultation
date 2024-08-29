from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from .serializers import *

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
        ]
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            username = request.data['username']
            password = request.data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return Response({'message': 'Авторизация успешна'}, status=status.HTTP_200_OK)
            return Response({'message': 'Неверные логин и/или пароль'}, status=status.HTTP_400_BAD_REQUEST)