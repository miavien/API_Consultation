from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from consultation_app.views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema

token_obtain_schema_view = extend_schema_view(
    post=extend_schema(
        tags=['For everyone'],
        summary='Получение JWT токена',
        description='Эндпоинт для получения JWT токена'
    )
)(TokenObtainPairView)

token_refresh_schema_view = extend_schema_view(
    post=extend_schema(
        tags=['For everyone'],
        summary='Обновление JWT токена',
        description='Эндпоинт для обновления JWT токена'
    )
)(TokenRefreshView)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('consultation_app.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/token/', token_obtain_schema_view.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', token_refresh_schema_view.as_view(), name='token_refresh'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('confirm/<str:token>/', ConfirmRegistrationAPIView.as_view(), name='confirm-registration'),
]
